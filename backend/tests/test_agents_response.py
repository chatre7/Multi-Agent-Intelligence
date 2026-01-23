
import sys
import os
import asyncio
from typing import List

# Setup path to import backend modules
# Assuming script is run from backend root or mapped volume
sys.path.append(os.getcwd())

try:
    from src.infrastructure.config.yaml_loader import YamlConfigLoader
    from src.infrastructure.persistence.in_memory.conversations import InMemoryConversationRepository
    from src.presentation.use_cases.chat.send_message import SendMessageUseCase, SendMessageRequest
    from src.infrastructure.llm.streaming import llm_from_env
    from src.infrastructure.langgraph.graph_builder import ConversationGraphBuilder
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this script from the 'backend' directory inside the container.")
    sys.exit(1)

async def test_agent(agent_id: str, domain_id: str):
    print(f"\n==================================================")
    print(f"Testing Agent: {agent_id} (Domain: {domain_id})")
    
    # Reload config for each test to be clean
    loader = YamlConfigLoader.from_default_backend_root()
    repo = InMemoryConversationRepository()
    
    # Initialize components
    try:
        use_case = SendMessageUseCase(
            loader=loader,
            graph_builder=ConversationGraphBuilder(),
            llm=llm_from_env(),
            conversation_repo=repo
        )
    except Exception as e:
        print(f"Setup Failed: {e}")
        return

    # Start conversation
    convo = repo.create_conversation(
        domain_id=domain_id,
        created_by_role="developer",
        created_by_sub="tester",
        title=f"Test {agent_id}"
    )
    
    # Get agent config to find trigger keyword
    bundle = loader.load_bundle()
    agent = bundle.agents.get(agent_id)
    if not agent:
        print(f"FAILED: Agent ID '{agent_id}' not found in configuration.")
        return

    # Construct prompt that forces the supervisor to pick this agent
    keywords = agent.keywords or []
    keyword = keywords[0] if keywords else f"talk to {agent_id}"
    
    # Force direct call if keyword logic is tricky? 
    # Supervisor logic: checks if keywords match user input.
    prompt = f"I want to {keyword} with {agent.name}. {agent.system_prompt[:50]}..."
    # Make it very obvious
    prompt = f"Please let me speak to {agent.name}. {keyword}."

    print(f"Input Prompt: '{prompt}'")
    print(f"Expected Model: {agent.model_name or 'DEFAULT'}")

    chunks = []
    agent_replied = False
    
    try:
        req = SendMessageRequest(
            domain_id=domain_id,
            message=prompt,
            role="developer",
            conversation_id=convo.id,
            subject="tester"
        )
        print("Streaming response...")
        async for event in use_case.stream(req):
            if event.type == "delta":
                print(event.text, end="", flush=True)
                chunks.append(event.text)
            elif event.type == "agent_selected":
                print(f"\n[Selected Agent: {event.agent_id}]")
                if event.agent_id != agent_id:
                     print(f"WARNING: Supervisor selected '{event.agent_id}' instead of '{agent_id}'")
            elif event.type == "done":
                agent_replied = True
    except Exception as e:
        print(f"\nEXECUTION ERROR: {e}")
        return

    response = "".join(chunks).strip()
    print("\n--------------------------------------------------")
    if not response:
        print(f"RESULT: FAIL (Empty response)")
    else:
        print(f"RESULT: PASS (Response length: {len(response)})")

async def main():
    # Define agents to test
    targets = [
        ("social_chat", "storyteller"),
        ("social_chat", "comedian"),
        ("social_chat", "philosopher"),
        ("social_chat", "empath"),
        ("software_development", "coder"),
        ("software_development", "debugger"), 
    ]
    
    print("Starting Agent Unit Tests...")
    for domain, agent in targets:
        await test_agent(agent, domain)
    print("\nAll tests completed.")

if __name__ == "__main__":
    asyncio.run(main())
