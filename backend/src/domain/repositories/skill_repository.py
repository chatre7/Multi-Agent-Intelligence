from abc import ABC, abstractmethod
from src.domain.entities.skill import Skill

class ISkillRepository(ABC):
    @abstractmethod
    def save(self, skill: Skill) -> None:
        pass
        
    @abstractmethod
    def get(self, skill_id: str) -> Skill | None:
        pass
        
    @abstractmethod
    def list_all(self) -> list[Skill]:
        pass
        
    @abstractmethod
    def delete(self, skill_id: str) -> None:
        pass
    
    @abstractmethod
    def add_skill_to_agent(self, agent_id: str, skill_id: str) -> None:
        pass
        
    @abstractmethod
    def remove_skill_from_agent(self, agent_id: str, skill_id: str) -> None:
        pass
        
    @abstractmethod
    def get_agent_skills(self, agent_id: str) -> list[Skill]:
        pass
