# chat.py
"""Chat Node"""

from typing import List, cast
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain.tools import tool
from copilotkit.langchain import copilotkit_customize_config
from research_canvas.state import AgentState
from research_canvas.model import get_model
from research_canvas.download import get_resource

@tool
def Search(queries: List[str]):  # pylint: disable=invalid-name,unused-argument
    """A list of one or more search queries to find good resources to support the research."""

@tool
def ArxivSearch(queries: List[str]):  # pylint: disable=invalid-name,unused-argument
    """A list of one or more search queries to find academic resources from Arxiv."""

@tool
def WriteReport(report: str):  # pylint: disable=invalid-name,unused-argument
    """Write the research report."""

@tool
def WriteResearchQuestion(research_question: str):  # pylint: disable=invalid-name,unused-argument
    """Write the research question."""

@tool
def DeleteResources(urls: List[str]):  # pylint: disable=invalid-name,unused-argument
    """Delete the URLs from the resources."""

@tool
def DocumentSelection():  # Tool for document selection
    """Retrieve available documents for research with presigned URLs."""

@tool
def RAGQuery(query: str, publication_id: int):  # Tool for RAG-based document querying
    """Retrieve information based on the content of a specific document."""

async def chat_node(state: AgentState, config: RunnableConfig):
    """
    Chat Node
    """
    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[
            {"state_key": "report", "tool": "WriteReport", "tool_argument": "report"},
            {"state_key": "research_question", "tool": "WriteResearchQuestion", "tool_argument": "research_question"},
        ],
        emit_tool_calls=["DeleteResources", "DocumentSelection", "RAGQuery"]
    )

    # Retrieve or initialize state variables
    state["resources"] = state.get("resources", [])
    research_question = state.get("research_question", "")
    report = state.get("report", "")
    document_list = state.get("document_list", [])  # Retrieve document list if available
    selected_document_id = state.get("selected_document_id")  # Retrieve selected document ID if available

    resources = []
    for resource in state["resources"]:
        content = get_resource(resource["url"])
        if content != "ERROR":
            resources.append({**resource, "content": content})

    model = get_model(state)
    ainvoke_kwargs = {}
    if model.__class__.__name__ == "ChatOpenAI":
        ainvoke_kwargs["parallel_tool_calls"] = False

    # Check if document list is available in state, else call DocumentSelection
    if not document_list:
        print("Document list not found in state. Emitting DocumentSelection tool call.")
        response = await model.bind_tools([DocumentSelection]).ainvoke(
            [SystemMessage(content="Retrieve available documents for research.")], config
        )
        return {"messages": response}

    # Format available documents as a string for the SystemMessage
    documents_display = "\n".join(
        [f"- {doc['title']} (ID: {doc['id']}, [Download Link]({doc['pdf_link']}))" for doc in document_list]
    )

    # Check if there’s a selected document for RAG queries
    last_message = state["messages"][-1].content.lower()
    if selected_document_id and "question" in last_message:
        print(f"Detected question context with document ID {selected_document_id}. Emitting RAGQuery tool call.")
        # Use the last message content as the question
        response = await model.bind_tools([RAGQuery]).ainvoke(
            [SystemMessage(content=f"Retrieve information about '{last_message}' from document ID {selected_document_id}.")],
            config
        )
        return {"messages": response}

    # Otherwise, proceed with the main model response
    response = await model.bind_tools(
        [Search, ArxivSearch, WriteReport, WriteResearchQuestion, DeleteResources, DocumentSelection, RAGQuery],
        **ainvoke_kwargs
    ).ainvoke([
        SystemMessage(
            content=f"""
            You are a research assistant helping with writing a research report, finding relevant documents, and answering specific questions based on document content.

            Guidelines:
            - **Document Selection**: If preprocessed publications are unavailable in the state, use `DocumentSelection` to retrieve them. Once selected, remember the document ID for further queries.
            - **RAGQuery (Retrieval-Augmented Generation)**: Use `RAGQuery` to answer questions about a specific document. Ensure the response indicates that content is based on the selected document's context.
            - **Arxiv Search**: For academic research papers, use `ArxivSearch` to find relevant resources on Arxiv.
            - **Web Search**: For general research beyond selected documents, use the `Search` tool to gather additional resources online.
            - **Report Writing**: Use `WriteReport` for adding content to the report. Only use this tool to add information to the report; avoid direct responses with report text. Engage the user by suggesting next steps or areas for improvement.

            Current research question:
            {research_question}

            Current research report:
            {report}

            Available resources (URLs and content):
            {resources}

            Preprocessed documents for selection:
            {documents_display}
            """
        ),
        *state["messages"],
    ], config)

    ai_message = cast(AIMessage, response)

    if ai_message.tool_calls:
        if ai_message.tool_calls[0]["name"] == "WriteReport":
            report = ai_message.tool_calls[0]["args"].get("report", "")
            return {
                "report": report,
                "messages": [ai_message, ToolMessage(
                    tool_call_id=ai_message.tool_calls[0]["id"],
                    content="Report written."
                )]
            }
        if ai_message.tool_calls[0]["name"] == "WriteResearchQuestion":
            return {
                "research_question": ai_message.tool_calls[0]["args"]["research_question"],
                "messages": [ai_message, ToolMessage(
                    tool_call_id=ai_message.tool_calls[0]["id"],
                    content="Research question written."
                )]
            }

    return {
        "messages": response
    }
