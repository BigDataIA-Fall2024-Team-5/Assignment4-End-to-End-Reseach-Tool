from langgraph.graph import StateGraph, END
from research_canvas.state import AgentState
from research_canvas.chat import chat_node
from research_canvas.download import download_node
from research_canvas.search import search_node
from research_canvas.rag_node import rag_node
from langchain_core.messages import AIMessage, ToolMessage
from typing import cast

# Define a new graph for your research agent.
workflow = StateGraph(AgentState)

# Add nodes (tasks) to the graph.
workflow.add_node("download", download_node)  # Download documents from S3
workflow.add_node("chat_node", chat_node)     # Handle user interaction and LLM responses
workflow.add_node("search_node", search_node) # Perform web or Arxiv searches
workflow.add_node("rag_node", rag_node)       # Add RAG node to retrieve document chunks

# Set 'download' as the entry point of your graph.
workflow.set_entry_point("download")

# Define routing logic based on tool calls or user input.
def route(state):
    """Route after the chat node based on tool calls."""
    messages = state.get("messages", [])
    
    if messages and isinstance(messages[-1], AIMessage):
        ai_message = cast(AIMessage, messages[-1])

        if ai_message.tool_calls:
            tool_name = ai_message.tool_calls[0]["name"]
            
            if tool_name == "Arxiv":
                return "arxiv_node"
                
            elif tool_name == "WebSearch":
                return "web_search_node"
                
            elif tool_name == "RAG":
                return "rag_node"  # Route to RAG node
                
            elif tool_name == "Search":
                return "search_node"

    if messages and isinstance(messages[-1], ToolMessage):
        return "chat_node"

    return END

# Add conditional edges based on routing logic.
workflow.add_conditional_edges("chat_node", route, ["search_node", "chat_node", "rag_node", END])

# Compile the graph.
graph = workflow.compile()