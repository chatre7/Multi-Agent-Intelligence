import uuid
from datetime import datetime
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.domain.entities.knowledge import KnowledgeDocument
from src.domain.repositories.knowledge_repository import IKnowledgeRepository
from src.infrastructure.persistence.chroma.knowledge_repository import ChromaKnowledgeRepository

class UploadKnowledgeUseCase:
    """Use case for uploading and processing knowledge documents."""

    def __init__(
        self,
        sqlite_repo: IKnowledgeRepository,
        chroma_repo: ChromaKnowledgeRepository
    ):
        self._sqlite_repo = sqlite_repo
        self._chroma_repo = chroma_repo
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def execute(self, filename: str, content: str, content_type: str) -> KnowledgeDocument:
        doc_id = str(uuid.uuid4())
        
        # 1. Create Document Entity
        doc = KnowledgeDocument(
            id=doc_id,
            filename=filename,
            content=content,  # Store full content in SQLite? Maybe truncate if too large for generic DB.
                              # For MVP we store it. In prod, maybe S3 + reference.
            content_type=content_type,
            size_bytes=len(content.encode('utf-8')),
            created_at=datetime.now(),
            status="processing"
        )
        
        # 2. Save metadata to SQLite
        self._sqlite_repo.save(doc)
        
        try:
            # 3. Chunk Content
            chunks = self._splitter.split_text(content)
            
            # 4. Embed and Save to Chroma
            metadatas = [{"document_id": doc_id, "source": filename, "chunk_index": i} for i in range(len(chunks))]
            self._chroma_repo.add_documents(texts=chunks, metadatas=metadatas)
            
            # 5. Update Status
            doc.status = "processed"
            self._sqlite_repo.save(doc)
            
        except Exception as e:
            # Rollback or mark failed
            doc.status = f"failed: {str(e)}"
            self._sqlite_repo.save(doc)
            raise e
            
        return doc

class ListKnowledgeUseCase:
    def __init__(self, repo: IKnowledgeRepository):
        self._repo = repo

    def execute(self) -> List[KnowledgeDocument]:
        return self._repo.list_all()

class DeleteKnowledgeUseCase:
    def __init__(
        self, 
        sqlite_repo: IKnowledgeRepository,
        chroma_repo: ChromaKnowledgeRepository
    ):
        self._sqlite_repo = sqlite_repo
        self._chroma_repo = chroma_repo

    def execute(self, document_id: str) -> None:
        self._sqlite_repo.delete(document_id)
        self._chroma_repo.delete_by_document_id(document_id)
