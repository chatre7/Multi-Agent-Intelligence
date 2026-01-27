import pytest
from src.infrastructure.persistence.sqlite.skills import SqliteSkillRepository
from src.domain.entities.skill import Skill

@pytest.fixture
def repo(tmp_path):
    # Use disk db to verify persistence, or memory
    db_path = str(tmp_path / "skills.db")
    return SqliteSkillRepository(db_path)

def test_crud_skill(repo):
    skill = Skill(id="s1", name="Test Skill", version="1.0.0", description="Desc", instructions="Do X")
    repo.save(skill)
    
    fetched = repo.get("s1")
    assert fetched is not None
    assert fetched.name == "Test Skill"
    assert fetched.instructions == "Do X"
    
    # Update
    skill.name = "Updated Skill"
    repo.save(skill)
    assert repo.get("s1").name == "Updated Skill"
    
    # List
    repo.save(Skill(id="s2", name="A Skill", version="1.0", description="", instructions=""))
    all_skills = repo.list_all()
    assert len(all_skills) == 2
    # Sorted by name (A Skill, Updated Skill)
    assert all_skills[0].id == "s2"
    
    # Delete
    repo.delete("s1")
    assert repo.get("s1") is None

def test_agent_skills(repo):
    skill1 = Skill(id="python", name="Python", version="1.0", description="", instructions="")
    skill2 = Skill(id="docker", name="Docker", version="1.0", description="", instructions="")
    repo.save(skill1)
    repo.save(skill2)
    
    agent_id = "agent-007"
    
    # Link
    repo.add_skill_to_agent(agent_id, "python")
    repo.add_skill_to_agent(agent_id, "docker")
    
    # Get
    skills = repo.get_agent_skills(agent_id)
    assert len(skills) == 2
    ids = {s.id for s in skills}
    assert "python" in ids
    assert "docker" in ids
    
    # Unlink
    repo.remove_skill_from_agent(agent_id, "python")
    skills = repo.get_agent_skills(agent_id)
    assert len(skills) == 1
    assert skills[0].id == "docker"

def test_cascade_delete(repo):
    """Test that deleting a skill removes it from agent links."""
    skill = Skill(id="cascade", name="Cascade", version="1.0", description="", instructions="")
    repo.save(skill)
    agent_id = "agent-X"
    repo.add_skill_to_agent(agent_id, "cascade")
    
    assert len(repo.get_agent_skills(agent_id)) == 1
    
    repo.delete("cascade")
    
    # Should stay empty or handle gracefully
    assert len(repo.get_agent_skills(agent_id)) == 0
