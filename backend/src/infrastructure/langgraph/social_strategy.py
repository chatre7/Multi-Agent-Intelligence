from typing import Dict, Any, List, Optional, Callable

from src.infrastructure.langgraph.workflow_strategies import WorkflowStrategy, WorkflowResult, WorkflowStep
from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig

from src.infrastructure.llm.streaming import llm_from_env

class SocialSimulationStrategy(WorkflowStrategy):
    """
    Strategy for autonomous AI-to-AI social interaction loops.
    
    This strategy simulates a social media environment (like Threads or Twitter)
    where multiple agents interact in a single conversation thread.
    
    Logic Flow:
    1. Select an agent to "post" or "reply" based on a turn-based loop.
    2. Build a prompt that includes the thread history and the specific agent's persona.
    3. LLM generates a post, including simulated metadata (like <likes>).
    4. Metadata is parsed and stored to be rendered as social widgets in the UI.
    
    Naming Note: Named 'social_strategy' instead of 'threads_strategy' to keep
    the logic decoupled from the specific 'Threads' UI, allowing it to be reused
    for any multi-agent social simulation (e.g., simulated debates, group chats).
    """
    
    def __init__(self):
        import random
        import json
        self.random = random
        self.json = json
        self.llm = llm_from_env()
        self.max_turns = 5 # default, can be overridden by domain config

    def execute(
        self,
        domain: DomainConfig,
        agents: dict[str, Agent],
        user_request: str,
        token_callback: Optional[Callable[[str], None]] = None,
        enable_thinking: bool = False,
    ) -> WorkflowResult:
        """
        Runs the simulation loop for a set number of turns.
        
        Args:
            domain: The domain config (contains simulation settings like max_turns).
            agents: Map of available agents participating in the social network.
            user_request: The "Topic" or "Seed Post" that starts the thread.
            token_callback: Optional streaming callback for real-time updates.
            enable_thinking: Whether to allow agents to output reasoning blocks.
            
        Returns:
            WorkflowResult containing a list of WorkflowSteps (each step is a social post).
        """
        
        # 0. Setup
        steps: List[WorkflowStep] = []
        topic = user_request
        
        # Filter agents to only those defined in the domain
        participating_agent_ids = domain.agents
        agent_list = [agents[aid] for aid in participating_agent_ids if aid in agents]
        
        if not agent_list:
            print(f"[WARN] SocialSimulationStrategy: No agents found for domain {domain.id}. Falling back to all available agents.")
            agent_list = list(agents.values())
        else:
            print(f"[INFO] SocialSimulationStrategy: Participating agents: {[a.id for a in agent_list]}")

        # Shuffle agents once at the start to make the order semi-random but balanced
        self.random.shuffle(agent_list)

        social_config = domain.metadata.get("social_simulation", {})
        max_turns = social_config.get("max_turns", self.max_turns)
        
        simulated_history = [
            {"role": "user", "content": topic, "name": "Admin"}
        ]
        
        # 1. Simulation Loop
        for turn in range(max_turns):
            # Select Next Speaker using Round-Robin approach to ensure variety
            next_agent = agent_list[turn % len(agent_list)]
            
            # Generate Prompt
            system_prompt, messages = self._build_prompt(next_agent, topic, simulated_history)
            
            # Generate Prompt
            system_prompt, messages = self._build_prompt(next_agent, topic, simulated_history)
            
            # Use Structured Output
            from src.domain.entities.schemas import SocialPost
            
            print(f"[DEBUG] Invoking Social Agent (Structured): {next_agent.id}")
            post_model = self.llm.structured_chat(
                model=next_agent.model_name or "default",
                system_prompt=system_prompt,
                messages=messages,
                response_model=SocialPost,
                temperature=0.7,
                max_tokens=500
            )
            
            content = post_model.content
            likes = post_model.likes
            
            # Wrap in JSON to preserve metadata through graph_builder's message mapping
            post_payload = {
                "content": content,
                "item_id": f"post_{turn}_{self.random.randint(1000,9999)}",
                "likes": likes,
                "author": {
                    "name": next_agent.name,
                    "handle": next_agent.metadata.get("handle") or f"@{next_agent.name.lower().replace(' ', '_')}",
                    "id": next_agent.id
                }
            }
            json_content = self.json.dumps(post_payload)
            
            # Record Step
            step = WorkflowStep(
                agent_id=next_agent.id,
                task=f"Turn {turn+1}",
                metadata={
                    "result": json_content,
                    "likes": likes,
                    "agent_name": next_agent.name,
                    "role": next_agent.description or "AI Agent",
                    "handle": next_agent.metadata.get("handle") or f"@{next_agent.name.lower().replace(' ', '_')}",
                    "thoughts": [{"content": post_model.thought, "type": "reasoning"}]
                }
            )
            steps.append(step)
            
            # Update Simulated History
            simulated_history.append({
                "role": "assistant",
                "content": content,
                "name": next_agent.name
            })
            
            # Optional: Emit a token to callback
            if token_callback:
                token_callback(f"\n\n**@{step.metadata['handle']}**: {content}")

        # 2. Final Result
        final_summary = "Social simulation complete."
        
        return WorkflowResult(
            steps=steps,
            final_response=final_summary,
            metadata={"simulation_topic": topic}
        )

    def _build_prompt(self, agent: Agent, topic: str, history: List[Dict]) -> tuple[str, List[Dict[str, str]]]:
        system_prompt = f"""
        IDENTITY:
        You are {agent.name}. {agent.system_prompt}
        
        TASK:
        Reply to the social media thread regarding the topic: "{topic}".
        
        RULES:
        - Keep it very short (max 280 characters).
        - Use a "{agent.name}" personality.
        - Respond in Thai if the topic is in Thai.
        """
        
        msgs = []
        
        # Add limited history context
        for h in history[-3:]:
            if h['role'] == 'user':
                msgs.append({"role": "user", "content": h['content']})
            else:
                msgs.append({"role": "assistant", "content": f"{h['name']}: {h['content']}"})
                 
        return system_prompt, msgs
