import requests
import re

# Regex pattern to extract the abstract from the HTML response
abstract_pattern = re.compile(
    r'<blockquote class="abstract mathjax">\s*<span class="descriptor">Abstract:</span>\s*(.*?)\s*</blockquote>',
    re.DOTALL
)

# Minimal version of AgentState (a simple dictionary substitute)
class AgentState(dict):
    pass

def arxiv_agent(state: AgentState) -> AgentState:
    """
    Fetches the abstract of a paper from arXiv using its paper ID.
    """
    arxiv_id = state.get("arxiv_id")  # Retrieve arxiv_id from the state

    if not arxiv_id:
        state["arxiv_result"] = {"arxiv_id": None, "error": "No arxiv_id provided."}
        return state

    try:
        # Fetch paper
        response = requests.get(f"https://export.arxiv.org/abs/{arxiv_id}")
        response.raise_for_status()

        # Extract abstract
        match = abstract_pattern.search(response.text)
        if match:
            state["arxiv_result"] = {
                "arxiv_id": arxiv_id,
                "abstract": match.group(1).strip()
            }
        else:
            state["arxiv_result"] = {"arxiv_id": arxiv_id, "error": "Abstract not found."}
    except requests.RequestException as e:
        state["arxiv_result"] = {"arxiv_id": arxiv_id, "error": str(e)}

    return state

# Testing the function for arxiv_id 2409.18475
state = AgentState()
state["arxiv_id"] = "2409.18475"

# Call the arxiv_agent function and print the result
updated_state = arxiv_agent(state)
print("Result for arxiv_id 2409.18475:", updated_state["arxiv_result"])
