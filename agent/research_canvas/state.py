# state.py
"""
This is the state definition for the AI.
It defines the state of the agent and the state of the conversation.
"""

from typing import List, TypedDict, Optional
from langgraph.graph import MessagesState

class Resource(TypedDict):
    """
    Represents a resource. Give it a good title and a short description.
    """
    url: str
    title: str
    description: str

class Log(TypedDict):
    """
    Represents a log of an action performed by the agent.
    """
    message: str
    done: bool

class Document(TypedDict):
    """
    Represents a document with an ID, title, and presigned URL.
    """
    id: int
    title: str
    pdf_link: str

class RAGResult(TypedDict):
    """
    Represents a RAG (Retrieval-Augmented Generation) query result.
    """
    id: str
    text: str
    metadata: dict

class AgentState(MessagesState):
    """
    This is the state of the agent.
    It is a subclass of the MessagesState class from langgraph.
    """
    model: str
    research_question: str
    report: str
    resources: List[Resource]
    logs: List[Log]
    document_list: Optional[List[Document]]  # Stores available documents for selection
    rag_query_result: Optional[List[RAGResult]]  # Stores results from RAG queries
