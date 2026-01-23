"""Utilities for processing and extracting facts from conversations."""

from typing import List
from src.infrastructure.llm.streaming import StreamingLLM

def extract_facts_prompt(conversation_text: str) -> str:
    """System prompt for fact extraction."""
    return f"""
You are an expert at distilling conversations into concise, atomic factual statements for long-term memory.

CONVERSATION:
{conversation_text}

TASK:
Identify any permanent facts about the user, their preferences, project details, or specific decisions made in this conversation.
Provide them as a list of short, independent sentences.
If no new important facts are found, respond with "NONE".

EXAMPLES:
- User is a senior developer who prefers Python over Java.
- The project name is 'Eternal-Agent-Recall'.
- We decided to use ChromaDB for vector storage.

Respond ONLY with the facts or "NONE".
"""

def extract_facts(llm: StreamingLLM, model: str, messages: List[dict]) -> List[str]:
    """Use LLM to extract facts from the latest turn of conversation."""
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-4:]]) # Look at last few turns
    
    prompt = extract_facts_prompt(conversation_text)
    
    # We use stream_chat but collect it fully since we need the final list
    response_gen = llm.stream_chat(
        model=model,
        system_prompt="You are a factual extraction assistant.",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500
    )
    
    full_response = "".join(list(response_gen)).strip()
    
    if full_response.upper() == "NONE" or not full_response:
        return []
    
    # Simple split by lines/bullets
    facts = []
    for line in full_response.split("\n"):
        clean_line = line.strip().lstrip("- ").lstrip("* ").strip()
        if clean_line:
            facts.append(clean_line)
    return facts
