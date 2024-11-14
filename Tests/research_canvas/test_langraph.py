import asyncio
from research_canvas.agent import graph
from research_canvas.state import AgentState

# Define an initial state for testing.
initial_state = AgentState(
    model="openai",
    research_question="What are the latest developments in quantum computing?",
    report="",
    resources=[],  # This will be populated by download or search nodes.
    logs=[],
    messages=[]
)

# Use asynchronous invocation because download_node is async.
async def run_graph():
    final_state = await graph.ainvoke(initial_state)
    
    # Print out final report or conversation history.
    print(f"Final Report: {final_state['report']}")
    print(f"Conversation History: {final_state['messages']}")

# Run the async function using asyncio.
asyncio.run(run_graph())