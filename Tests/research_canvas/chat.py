from langchain_core.messages import SystemMessage
from langchain.tools import Tool
from research_canvas.state import AgentState
from research_canvas.model import get_model
# Placeholder tool definitions
SearchTool = Tool(name="Search", func=lambda x: "Searching...", description="Search tool")
WriteReportTool = Tool(name="WriteReport", func=lambda x: "Writing report...", description="Write report tool")
DeleteResourcesTool = Tool(name="DeleteResources", func=lambda x: "Deleting resources...", description="Delete resources tool")
async def chat_node(state: AgentState, config):
   """Handle user interaction and LLM responses."""
   
   model = get_model(state)  # Get LLM model
   
   response = await model.bind_tools(
       [SearchTool(), WriteReportTool(), DeleteResourcesTool()],
       parallel_tool_calls=False  # Adjust based on model capabilities
   ).ainvoke([
       SystemMessage(
           content=f"""
           You are a research assistant helping with writing a research report.
           Use available tools like Arxiv search or web search to gather information.
           
           Research Question: {state.get('research_question')}
           Resources: {state.get('resources')}
           """
       ),
       *state["messages"],
   ], config)
   
   state["messages"].append(response)  # Append response to conversation history
   
   return state