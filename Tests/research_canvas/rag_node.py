import os
from langchain_pinecone import PineconeVectorStore
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings  # Use NVIDIA embeddings
from langchain_core.messages import AIMessage, SystemMessage
from research_canvas.state import AgentState
async def rag_node(state: AgentState, config):
    """RAG Agent: Retrieve relevant document chunks from Pinecone and generate answers."""
    
    # Initialize Pinecone client (ensure you're using the correct index name)
    pinecone_index = PineconeVectorStore.from_existing_index(
        index_name="your_index_name",  # Replace with your actual index name
        embedding=NVIDIAEmbeddings(
            model="nvidia/nv-embedqa-e5-v5",  # Same model as used in Airflow pipeline
            api_key=os.getenv("NVIDIA_API_KEY"),
            truncate="END"
        )
    )
    
    # Get user query from state
    query = state.get("research_question")
    
    # Embed the user query using NVIDIA embeddings
    embedding_client = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.getenv("NVIDIA_API_KEY"),
        truncate="END"
    )
    
    query_embedding = embedding_client.embed_query(query)
    
    # Retrieve relevant chunks from Pinecone based on similarity search
    results = pinecone_index.similarity_search_by_vector(query_embedding, k=5)
    
    # Generate a response using retrieved chunks
    retrieved_texts = [result['text'] for result in results]
    
    response_content = f"Based on the documents, here are some insights:\n\n" + "\n\n".join(retrieved_texts)
    
    # Update state with generated response
    state["messages"].append(AIMessage(content=response_content))
    
    return state