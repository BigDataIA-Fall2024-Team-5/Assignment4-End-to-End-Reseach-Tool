from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import snowflake.connector
from io import BytesIO
from urllib.parse import urlparse
from dotenv import load_dotenv
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker
from requests.exceptions import HTTPError

# Load environment variables
load_dotenv()

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def fetch_pdf_data_from_snowflake(**kwargs):
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
    query = f"SELECT id, title, pdf_link FROM {table_name};"
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    kwargs['ti'].xcom_push(key='pdf_data', value=records)

def parse_s3_url(s3_url):
    parsed_url = urlparse(s3_url)
    bucket = parsed_url.netloc.split('.')[0]
    key = parsed_url.path.lstrip('/')
    return bucket, key

def process_and_chunk_pdf(pdf_link, title, id, **kwargs):
    from docling.document_converter import DocumentConverter
    from docling_core.transforms.chunker import HierarchicalChunker
    import boto3

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv("AWS_REGION")
    )
    
    bucket, key = parse_s3_url(pdf_link)
    pdf_obj = s3.get_object(Bucket=bucket, Key=key)
    pdf_content = pdf_obj['Body'].read()
    pdf_stream = DocumentStream(name=os.path.basename(key), stream=BytesIO(pdf_content))
    
    converter = DocumentConverter()
    docling_result = converter.convert(pdf_stream)
    markdown_content = docling_result.document.export_to_markdown()
    
    markdown_key = f"processed/dockling/{os.path.basename(key).replace('.pdf', '.md')}"
    s3.put_object(Bucket=bucket, Key=markdown_key, Body=markdown_content.encode('utf-8'))
    chunker = HierarchicalChunker()
    chunks = list(chunker.chunk(docling_result.document))
    chunk_texts = [chunk.text for chunk in chunks]
    kwargs['ti'].xcom_push(key=f'chunks_{id}', value=chunk_texts)

def create_index_in_pinecone(id, title, **kwargs):
    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
    from langchain_pinecone import PineconeVectorStore
    from pinecone import Pinecone as PineconeClient, ServerlessSpec

    embedding_client = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.getenv("NVIDIA_API_KEY"),
        truncate="END"
    )
    pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))
    index_name = f"pdf-index-{id}"
    
    if index_name in pc.list_indexes().names():
        pc.delete_index(index_name)
    
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    
    pinecone_index = pc.Index(index_name)
    vector_store = PineconeVectorStore(index=pinecone_index, embedding=embedding_client)
    chunks = kwargs['ti'].xcom_pull(key=f'chunks_{id}')
    
    documents = []
    for i, chunk in enumerate(chunks):
        try:
            embedding = embedding_client.embed_query(chunk)
            document = {
                "id": f"{id}-{i}",
                "text": chunk,
                "embedding": embedding,
                "metadata": {"title": title}
            }
            documents.append(document)
        except HTTPError as e:
            if "expired" in str(e).lower():
                print(f"Error: NVIDIA API credits expired.")
                break
    vector_store.add_texts([doc['text'] for doc in documents], embeddings=[doc['embedding'] for doc in documents])

with DAG(
    'pdf_processing_pipeline',
    default_args=default_args,
    description='DAG for processing PDFs, converting to Markdown, chunking, and indexing in Pinecone',
    schedule_interval=None,
    start_date=datetime(2024, 11, 11),
    catchup=False
) as dag:

    fetch_data_task = PythonOperator(
        task_id='fetch_pdf_data_from_snowflake',
        python_callable=fetch_pdf_data_from_snowflake,
        provide_context=True
    )

    def process_all_pdfs(**kwargs):
        pdf_data = kwargs['ti'].xcom_pull(key='pdf_data')
        for id, title, pdf_link in pdf_data:
            process_and_chunk_pdf(pdf_link, title, id, **kwargs)

    process_data_task = PythonOperator(
        task_id='process_pdfs',
        python_callable=process_all_pdfs,
        provide_context=True
    )

    def index_all_pdfs(**kwargs):
        pdf_data = kwargs['ti'].xcom_pull(key='pdf_data')
        for id, title, _ in pdf_data:
            create_index_in_pinecone(id, title, **kwargs)

    index_data_task = PythonOperator(
        task_id='index_pinecone',
        python_callable=index_all_pdfs,
        provide_context=True
    )

    fetch_data_task >> process_data_task >> index_data_task
