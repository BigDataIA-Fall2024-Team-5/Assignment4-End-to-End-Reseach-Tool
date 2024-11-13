from langchain_community.tools import ArxivQueryRun
from research_canvas.state import AgentState
async def search_node(state: AgentState, config):
    """Perform web or Arxiv searches."""
    
    queries = state.get("queries")  # Get search queries from state
    
    search_results = []
    
    arxiv_tool = ArxivQueryRun()
    
    for query in queries:
        result = arxiv_tool.run(query)  # Perform Arxiv search
        search_results.append(result)
        
        print(f"Search result for query '{query}': {result}")
    
    # Update state with search results
    state["resources"].extend(search_results)
    
    return state