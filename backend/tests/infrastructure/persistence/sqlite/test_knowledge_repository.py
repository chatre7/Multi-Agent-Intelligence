import os
import pytest
from src.domain.entities.knowledge import KnowledgeDocument
from src.infrastructure.persistence.sqlite.knowledge_repository import SqliteKnowledgeRepository
from src.infrastructure.persistence.sqlite.schema import init_schema

@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test_knowledge.db"
    # :memory: URI works but typically we test with file path for sqlite to mimic prod better or use uri="file::memory:?cache=shared"
    # Using disk file for simplicity in debugging
    repo = SqliteKnowledgeRepository(str(db_path))
    # Basic schema init - normally done in __post_init__ or via migration tool
    # Check if repo inits its own schema. Based on skills implementation it does.
    return repo

def test_save_and_get(repo):
    doc = KnowledgeDocument(
        id="doc1",
        filename="test.txt",
        content="Test Content",
        content_type="text/plain",
        size_bytes=12
    )
    repo.save(doc)
    
    saved = repo.get_by_id("doc1")
    assert saved is not None
    assert saved.id == "doc1"
    assert saved.filename == "test.txt"
    assert saved.content_type == "text/plain"
    
def test_list_all(repo):
    repo.save(KnowledgeDocument(id="1", filename="a.txt", content="A", content_type="text", size_bytes=1))
    repo.save(KnowledgeDocument(id="2", filename="b.txt", content="B", content_type="text", size_bytes=1))
    
    docs = repo.list_all()
    assert len(docs) == 2
    assert {d.id for d in docs} == {"1", "2"}

def test_delete(repo):
    repo.save(KnowledgeDocument(id="del_me", filename="del.txt", content="del", content_type="text", size_bytes=3))
    assert repo.get_by_id("del_me") is not None
    
    repo.delete("del_me")
    assert repo.get_by_id("del_me") is None
