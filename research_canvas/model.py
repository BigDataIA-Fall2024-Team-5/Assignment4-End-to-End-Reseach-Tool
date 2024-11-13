# model.py

from langchain_core.language_models.chat_models import BaseChatModel

def get_model(state):
    """Get a model based on environment variable or state."""
    model_name = state.get("model", "openai")
    
    if model_name == "openai":
        # Replace with actual OpenAI model initialization
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(temperature=0)

    # Add other models here if needed (e.g., Anthropic, Google GenAI)
    
    raise ValueError(f"Unknown model: {model_name}")