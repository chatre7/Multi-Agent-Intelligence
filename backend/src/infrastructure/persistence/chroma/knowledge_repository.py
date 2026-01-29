import os
import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from langchain_chroma import Chroma
from src.infrastructure.llm.embeddings import get_embeddings

logger = logging.getLogger(__name__)

class ChromaKnowledgeRepository:
    """ChromaDB implementation for Knowledge Base vectors."""

    def __init__(
        self, 
        persist_directory: Optional[str] = None,
        collection_name: str = "agent_knowledge"
    ):
        if persist_directory is None:
            persist_directory = os.getenv("CHROMA_KNOWLEDGE_DIR", "/app/data/knowledge/chroma")
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        self._vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=get_embeddings(),
            persist_directory=persist_directory
        )

    def add_documents(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]], 
        ids: Optional[List[str]] = None
    ) -> None:
        if ids is None:
            ids = [str(uuid4()) for _ in texts]
        self._vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    def search_similar(
        self, 
        query: str, 
        limit: int = 5, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
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

    def delete_by_document_id(self, document_id: str) -> None:
        # Chroma doesn't support delete by metadata easily/efficiently in all versions, 
        # but modern versions support `where` filter on delete or get.
        # Ideally we store chunk IDs mapped to document IDs, but for MVP we might need to fetch IDs first.
        # This implementation assumes generic usage. Optimization: Fetch IDs where metadata['document_id'] == id then delete.
        try:
            # Fetch IDs to delete
            result = self._vectorstore.get(where={"document_id": document_id})
            if result and result['ids']:
                self._vectorstore.delete(ids=result['ids'])
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")

    def clear_all(self) -> None:
        try:
            self._vectorstore.delete_collection()
            # Re-init
            self._vectorstore = Chroma(
                collection_name=self._vectorstore._collection_name,
                embedding_function=self._vectorstore.embeddings,
                persist_directory=self._vectorstore._persist_directory
            )
        except Exception as e:
             logger.error(f"Failed to clear knowledge collection: {e}")
