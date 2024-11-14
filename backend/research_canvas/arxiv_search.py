# arxiv_search.py
"""
The arxiv_search node is responsible for searching Arxiv for research papers.
"""

import os
from typing import cast, List
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain.tools import tool
from copilotkit.langchain import copilotkit_emit_state, copilotkit_customize_config
from research_canvas.state import AgentState
from research_canvas.model import get_model
import arxiv

class ArxivResourceInput(BaseModel):
    """A resource representing an Arxiv paper with a short description"""
    url: str = Field(description="The URL of the paper")
    title: str = Field(description="The title of the paper")
    description: str = Field(description="A short abstract of the paper")

@tool
def ExtractArxivResources(resources: List[ArxivResourceInput]):  # pylint: disable=invalid-name,unused-argument
    """Extract the 3-5 most relevant papers from an Arxiv search result."""

async def arxiv_search_node(state: AgentState, config: RunnableConfig):
    """
    The arxiv_search node is responsible for searching Arxiv for research papers.
    """
    ai_message = cast(AIMessage, state["messages"][-1])

    state["resources"] = state.get("resources", [])
    state["logs"] = state.get("logs", [])
    queries = ai_message.tool_calls[0]["args"]["queries"]

    for query in queries:
        state["logs"].append({
            "message": f"Searching Arxiv for papers related to '{query}'",
            "done": False
        })

    await copilotkit_emit_state(config, state)

    arxiv_results = []

    for i, query in enumerate(queries):
        try:
            print(f"Executing Arxiv search with query: {query}")
            search = arxiv.Search(
                query=query,
                max_results=5,
                sort_by=arxiv.SortCriterion.Relevance
            )
            results = [
                {
                    "title": result.title,
                    "url": result.pdf_url,
                    "description": result.summary
                } for result in search.results()
            ]
            arxiv_results.extend(results)
            state["logs"][i]["done"] = True
            await copilotkit_emit_state(config, state)
        except Exception as e:
            print(f"An unexpected error occurred during Arxiv search for query '{query}': {e}")
            state["logs"][i]["message"] = f"Unexpected error: {str(e)}"
            state["logs"][i]["done"] = True
            await copilotkit_emit_state(config, state)

    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "resources",
            "tool": "ExtractArxivResources",
            "tool_argument": "resources",
        }],
    )

    model = get_model(state)
    ainvoke_kwargs = {}
    if model.__class__.__name__ in ["ChatOpenAI"]:
        ainvoke_kwargs["parallel_tool_calls"] = False

    # Figure out which resources to use
    response = await model.bind_tools(
        [ExtractArxivResources],
        tool_choice="ExtractArxivResources",
        **ainvoke_kwargs
    ).ainvoke([
        SystemMessage(
            content="You need to extract the 3-5 most relevant papers from the following Arxiv search results."
        ),
        *state["messages"],
        ToolMessage(
            tool_call_id=ai_message.tool_calls[0]["id"],
            content=f"Performed Arxiv search: {arxiv_results}"
        )
    ], config)

    state["logs"] = []
    await copilotkit_emit_state(config, state)

    ai_message_response = cast(AIMessage, response)
    resources = ai_message_response.tool_calls[0]["args"]["resources"]

    state["resources"].extend(resources)

    state["messages"].append(ToolMessage(
        tool_call_id=ai_message.tool_calls[0]["id"],
        content=f"Added the following Arxiv papers: {resources}"
    ))

    return state
