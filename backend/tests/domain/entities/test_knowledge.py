import pytest
from datetime import datetime
from src.domain.entities.knowledge import KnowledgeDocument

class TestKnowledgeDocument:
    def test_create_knowledge_document(self):
        doc = KnowledgeDocument(
            id="test-id",
            filename="test.txt",
            content="Hello World",
            content_type="text/plain",
            size_bytes=11,
            created_at=datetime.now()
        )
        assert doc.id == "test-id"
        assert doc.filename == "test.txt"
        assert doc.content == "Hello World"
        assert doc.status == "processed"  # Default status

    def test_knowledge_document_to_dict(self):
        doc = KnowledgeDocument(
            id="test-id",
            filename="test.txt",
            content="Hello World",
            content_type="text/plain",
            size_bytes=11
        )
        data = doc.to_dict()
        assert data["id"] == "test-id"
        assert data["filename"] == "test.txt"
        assert "content" not in data  # Content typically excluded from lightweight dicts or handled separately
