from typing import List, TypedDict,Annotated
from langgraph.graph.message import add_messages
class AgentState(TypedDict):
    model: str
    research_question: str
    report: str
    resources: List[dict]  # Holds document chunks or external resources
    logs: List[dict]       # Logs actions performed by agents
    messages: Annotated[list, add_messages]  # Keeps track of conversation history