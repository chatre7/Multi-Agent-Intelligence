import os
from typing import List, Dict, Any, Optional
from uuid import uuid4

from langchain_chroma import Chroma
from src.domain.repositories.memory_repository import IMemoryRepository
from src.infrastructure.llm.embeddings import get_embeddings

class ChromaMemoryRepository(IMemoryRepository):
    """ChromaDB implementation of long-term memory."""

    def __init__(
        self, 
        persist_directory: Optional[str] = None,
        collection_name: str = "agent_memories"
    ):
        if persist_directory is None:
            # Default to /app/data/memory/chroma inside container
            persist_directory = os.getenv("CHROMA_PERSIST_DIR", "/app/data/memory/chroma")
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        self._vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=get_embeddings(),
            persist_directory=persist_directory
        )

    def add_memories(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None, 
        ids: Optional[List[str]] = None
    ) -> None:
        if ids is None:
            ids = [str(uuid4()) for _ in texts]
        self._vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    def search_memories(
        self, 
        query: str, 
        limit: int = 5, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        print(f"[MEMORY] Searching for: {query}")
        results = self._vectorstore.similarity_search(
            query, k=limit, filter=filter
        )
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in results
        ]

    def delete_memories(self, ids: List[str]) -> None:
        self._vectorstore.delete(ids=ids)

    def clear_all(self) -> None:
        # In Chroma/LangChain, it's easier to just delete the collection or reset
        # For now, we'll delete all if we can get all IDs, or just delete the collection
        self._vectorstore.delete_collection()
        # Re-initialize after deletion
        self._vectorstore = Chroma(
            collection_name=self._vectorstore._collection_name,
            embedding_function=self._vectorstore.embeddings,
            persist_directory=self._vectorstore._persist_directory
        )
