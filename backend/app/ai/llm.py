import os 

from langchain_ollama import ChatOllama

def get_llm()-> ChatOllama:
    #Creating the local Ollama LLM used by the application

    model = os.getenv(
        "OLLAMA_MODEL",
        "qwen3:8b",
    )

    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434",
    )

    return ChatOllama(
        model = model,
        base_url = base_url,
        temperature = 0.0, #because we want to stick to the reality and want factual answers
    )