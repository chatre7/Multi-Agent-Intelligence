"""
Unit tests for Skills API endpoints.
"""

from unittest.mock import patch, Mock
import pytest
from fastapi.testclient import TestClient

from src.presentation.api.app import create_app
from src.domain.entities.skill import Skill

# Refactoring for cleaner mock access
@pytest.fixture
def mock_dependencies():
    with patch("src.presentation.api.app.YamlConfigLoader") as mock_yaml, \
         patch("src.presentation.api.app.SkillLoader") as mock_skill_loader, \
         patch("src.presentation.api.app.SqliteSkillRepository") as mock_skill_repo:
        
        # Default empty bundle
        mock_yaml.from_default_backend_root.return_value.load_bundle.return_value = Mock(domains={}, agents={}, tools={})
        
        # Loader returns items to be seeded
        mock_skill_loader.return_value.load_all_skills.return_value = []
        
        yield {
            "yaml": mock_yaml,
            "skill_loader": mock_skill_loader,
            "skill_repo": mock_skill_repo,
            "skill_repo_inst": mock_skill_repo.return_value
        }

@pytest.fixture
def client(mock_dependencies):
    # Mock AUTH_MODE to 'dev' (or anything not 'jwt') so that x-role header works
    # We must patch os.environ BEFORE create_app is called
    with patch.dict("os.environ", {"AUTH_MODE": "dev"}):
        app = create_app()
        return TestClient(app)

def test_list_skills_success(client, mock_dependencies):
    """Test GET /v1/skills returns list of skills."""
    # Setup Data on REPO (not loader anymore, as list_skills uses repo)
    mock_repo_inst = mock_dependencies["skill_repo_inst"]
    mock_repo_inst.list_all.return_value = [
        Skill(id="skill-1", name="Skill 1", version="1.0.0", description="Desc 1", instructions="Inst 1"),
        Skill(id="skill-2", name="Skill 2", version="2.0.0", description="Desc 2", instructions="Inst 2"),
    ]
    
    # Use x-role header (works because AUTH_MODE=dev)
    response = client.get("/v1/skills", headers={"x-role": "admin"})
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "skill-1"
    assert data[1]["name"] == "Skill 2"

def test_list_skills_empty(client, mock_dependencies):
    """Test GET /v1/skills returns empty list when no skills."""
    mock_instance = mock_dependencies["skill_repo_inst"]
    mock_instance.list_all.return_value = []
    
    response = client.get("/v1/skills", headers={"x-role": "admin"})
            
    assert response.status_code == 200
    assert response.json() == []

def test_list_skills_error_handling(client, mock_dependencies):
    """Test GET /v1/skills handles loader errors gracefully."""
    mock_instance = mock_dependencies["skill_repo_inst"]
    mock_instance.list_all.side_effect = Exception("Disk error")
    
    response = client.get("/v1/skills", headers={"x-role": "admin"})
            
    # Our implementation catches Exception and returns []
    assert response.status_code == 200
    assert response.json() == []
