# agent.py
# Add the necessary imports
from typing import cast
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from research_canvas.state import AgentState
from research_canvas.download import download_node
from research_canvas.chat import chat_node
from research_canvas.search import search_node
from research_canvas.delete import delete_node, perform_delete_node
from research_canvas.document_selection import document_selection_agent
from research_canvas.rag import rag_agent  # Ensure this imports your RAG agent

# Define the workflow
workflow = StateGraph(AgentState)

# Add nodes for basic operations
workflow.add_node("download", download_node)
workflow.add_node("chat_node", chat_node)
workflow.add_node("search_node", search_node)
workflow.add_node("delete_node", delete_node)
workflow.add_node("perform_delete_node", perform_delete_node)

# Add new agent nodes for document selection and RAG querying
workflow.add_node("document_selection_agent", document_selection_agent)
workflow.add_node("rag_agent", rag_agent)

# Define routing logic for handling specific tool calls
def route(state):
    messages = state.get("messages", [])
    if messages and isinstance(messages[-1], AIMessage):
        ai_message = cast(AIMessage, messages[-1])
        if ai_message.tool_calls:
            tool_name = ai_message.tool_calls[0]["name"]
            print(f"Routing based on tool call: {tool_name}")

            # Check tool call name and extract query/publication_id if needed
            if tool_name == "DocumentSelection":
                return "document_selection_agent"
            elif tool_name == "RAGQuery":
                # Extract query and publication_id from tool call args
                query = ai_message.tool_calls[0]["args"].get("query")
                publication_id = ai_message.tool_calls[0]["args"].get("publication_id")
                if query and publication_id:
                    # Store query and publication_id in state for rag_agent
                    state["query"] = query
                    state["publication_id"] = publication_id
                    return "rag_agent"
                else:
                    print("Error: query or publication_id missing in RAGQuery tool call.")
                    return END  # Handle this as an error case if values are missing
            elif tool_name == "Search":
                return "search_node"
            elif tool_name == "DeleteResources":
                return "delete_node"

    print("Defaulting to chat_node")
    return "chat_node" if messages and isinstance(messages[-1], ToolMessage) else END

# Initialize workflow with entry point and edges
memory = MemorySaver()
workflow.set_entry_point("download")
workflow.add_edge("download", "chat_node")
workflow.add_conditional_edges("chat_node", route, ["document_selection_agent", "rag_agent", "search_node", "delete_node", END])
workflow.add_edge("delete_node", "perform_delete_node")
workflow.add_edge("perform_delete_node", "chat_node")
workflow.add_edge("search_node", "download")
graph = workflow.compile(checkpointer=memory, interrupt_after=["delete_node"])
