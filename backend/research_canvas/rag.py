# rag.py

import os
from pinecone import Pinecone as PineconeClient
from langchain_pinecone import PineconeVectorStore
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from research_canvas.state import AgentState

# Initialize Pinecone and NVIDIA Embeddings clients
pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))
embedding_client = NVIDIAEmbeddings(
    model="nvidia/nv-embedqa-e5-v5",
    api_key=os.getenv("NVIDIA_API_KEY"),
    truncate="END"
)

def rag_agent(state: AgentState):
    """
    Queries a specific Pinecone index for a document based on publication_id.
    Updates the state with the RAG query results.
    """
    # Retrieve query and publication_id from state
    query = state.get("query")
    publication_id = state.get("publication_id")
    
    if not query or not publication_id:
        state["rag_query_result"] = {"error": "Missing query or publication ID."}
        return state

    index_name = f"pdf-index-{publication_id}"
    
    # Check if the index exists
    if index_name not in pc.list_indexes().names():
        state["rag_query_result"] = {"error": f"Index {index_name} does not exist in Pinecone."}
        return state
    
    # Initialize Pinecone index
    pinecone_index = pc.Index(index_name)
    
    # Initialize Pinecone vector store with the embedding client and Pinecone index
    vector_store = PineconeVectorStore(index=pinecone_index, embedding=embedding_client)
    
    # Embed the query using the embedding client
    query_embedding = embedding_client.embed_query(query)
    
    # Query Pinecone for similar documents
    response = vector_store.similarity_search(query_embedding, top_k=5)
    
    # Process the results
    results = [{"id": match["id"], "text": match["text"], "metadata": match.get("metadata", {})} for match in response]
    
    # Update the state with the RAG query result
    state["rag_query_result"] = {
        "publication_id": publication_id,
        "query": query,
        "results": results
    }
    return state
