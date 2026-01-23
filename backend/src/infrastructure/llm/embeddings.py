import os
from langchain_ollama import OllamaEmbeddings

def get_embeddings() -> OllamaEmbeddings:
    """Create OllamaEmbeddings from environment settings."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    return OllamaEmbeddings(base_url=base_url, model=model)
