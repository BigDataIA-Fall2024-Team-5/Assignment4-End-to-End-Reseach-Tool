import os
import snowflake.connector
import boto3
from io import BytesIO
from urllib.parse import urlparse
from dotenv import load_dotenv
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from requests.exceptions import HTTPError
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient, ServerlessSpec

# Load environment variables
load_dotenv()

# Initialize NVIDIA embedding client
embedding_client = NVIDIAEmbeddings(
    model="nvidia/nv-embedqa-e5-v5",
    api_key=os.getenv("NVIDIA_API_KEY"),
    truncate="END"
)

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv("AWS_REGION")
)

# Initialize Pinecone client
pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))

# Define Snowflake configurations
def fetch_pdf_data_from_snowflake():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WH_PUBLICATIONS_ETL"),
        database=os.getenv("SNOWFLAKE_DATABASE", "RESEARCH_PUBLICATIONS"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RESEARCH_PUBLICATIONS"),
        role=os.getenv("SNOWFLAKE_ROLE")
    )
    cursor = conn.cursor()

    table_name = os.getenv("SNOWFLAKE_TABLE", "PUBLICATION_LIST")

    # Include title in the query
    query = f"SELECT id, title, pdf_link FROM {table_name};"
    cursor.execute(query)
    records = cursor.fetchall()

    cursor.close()
    conn.close()
    return records

# Function to extract S3 bucket and key from the URL
def parse_s3_url(s3_url):
    parsed_url = urlparse(s3_url)
    bucket = parsed_url.netloc.split('.')[0]
    key = parsed_url.path.lstrip('/')
    return bucket, key

# Function to delete an existing index in Pinecone
def delete_existing_index(pdf_id):
    index_name = f"pdf-index-{pdf_id}"
    if index_name in pc.list_indexes().names():
        pc.delete_index(index_name)
        print(f"Deleted existing index: {index_name}")

# Process PDF, convert to Markdown, and chunk content
def process_and_chunk_pdf(pdf_link):
    bucket, key = parse_s3_url(pdf_link)
    
    # Download PDF from S3
    pdf_obj = s3.get_object(Bucket=bucket, Key=key)
    pdf_content = pdf_obj['Body'].read()
    pdf_stream = DocumentStream(name=os.path.basename(key), stream=BytesIO(pdf_content))
    
    # Process the PDF with Docling
    converter = DocumentConverter()
    docling_result = converter.convert(pdf_stream)
    
    # Export to Markdown
    markdown_content = docling_result.document.export_to_markdown()
    
    # Save the Markdown to S3 under processed/dockling/
    markdown_key = f"processed/dockling/{os.path.basename(key).replace('.pdf', '.md')}"
    s3.put_object(Bucket=bucket, Key=markdown_key, Body=markdown_content.encode('utf-8'))
    print(f"Markdown saved to S3 at {markdown_key}")

    # Chunk the document content for embedding
    chunker = HierarchicalChunker()
    chunks = list(chunker.chunk(docling_result.document))
    chunk_texts = [chunk.text for chunk in chunks]
    
    return chunk_texts

# Create or update index in Pinecone
def create_index_in_pinecone(id, title, chunks):
    index_name = f"pdf-index-{id}"
    
    # Delete existing index if it already exists
    delete_existing_index(id)
    
    # Create a new index using the updated Pinecone client
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1024,  # Adjust dimension as per model's embedding output
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    
    # Retrieve the index object from Pinecone
    pinecone_index = pc.Index(index_name)  # Correctly initialize the Pinecone index
    
    # Initialize Pinecone vector store with the embedding client and Pinecone index
    vector_store = PineconeVectorStore(index=pinecone_index, embedding=embedding_client)

    # Embed chunks and create documents with metadata
    documents = []
    for i, chunk in enumerate(chunks):
        try:
            embedding = embedding_client.embed_query(chunk)
            document = {
                "id": f"{id}-{i}",
                "text": chunk,
                "embedding": embedding,
                "metadata": {"title": title}  # Store title in metadata
            }
            documents.append(document)
        except HTTPError as e:
            if "expired" in str(e).lower():
                print(f"Error: NVIDIA API credits expired. Unable to process chunk {i} for document ID {id}.")
                break
            else:
                print(f"Error processing chunk {i} for document ID {id}: {e}")
    
    # Insert embedded documents into Pinecone
    vector_store.add_texts([doc['text'] for doc in documents], embeddings=[doc['embedding'] for doc in documents])

    print(f"Chunks for document {id} with title '{title}' indexed in Pinecone.")

# Full workflow for processing and indexing PDFs
def main():
    pdf_data = fetch_pdf_data_from_snowflake()
    
    for record in pdf_data:
        id, title, pdf_link = record
        print(f"Processing document ID {id} with title '{title}'")
        
        chunks = process_and_chunk_pdf(pdf_link)
        
        create_index_in_pinecone(id, title, chunks)

if __name__ == "__main__":
    main()
