"""Intent Classifier Component.

Separates intent classification from orchestrator following Microsoft's multi-agent architecture.
Routes user queries to appropriate specialized agents based on intent analysis.
"""

from typing import Literal, TypedDict, Dict, List, Optional
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama


class UserIntent(TypedDict):
    """The user's current intent in the conversation."""

    intent: Literal[
        "planner", "coder", "critic", "tester", "reviewer", "general", "unknown"
    ]
    confidence: float
    reasoning: str


class IntentClassifierConfig(BaseModel):
    """Configuration for the intent classifier."""

    model_name: str = "gpt-oss:120b-cloud"
    temperature: float = 0
    confidence_threshold: float = 0.6
    enable_fallback: bool = True


class IntentClassifier:
    """Separate intent classifier component for multi-agent routing.

    Follows Microsoft architecture by separating classification logic from orchestrator.
    Uses NLU/LLM cascade strategy for cost-effective routing.
    """

    def __init__(self, config: Optional[IntentClassifierConfig] = None):
        self.config = config or IntentClassifierConfig()
        self._model = ChatOllama(
            model=self.config.model_name,
            temperature=self.config.temperature,
            request_timeout=30.0,
        )

        self._agent_capabilities: Dict[str, str] = {
            "planner": "Complex task planning, breaking down requirements, strategy development",
            "coder": "Writing code, file creation, implementation, programming tasks",
            "critic": "Code review, quality assurance, logic validation, security checks",
            "tester": "Running tests, executing scripts, validation, debugging",
            "reviewer": "Final verification, output checking, results summarization",
            "general": "General questions, information, explanations, non-coding queries",
        }

    def _build_system_prompt(self) -> str:
        """Build system prompt for intent classification."""
        capabilities = "\n".join(
            f"- {k}: {v}" for k, v in self._agent_capabilities.items()
        )

        return f"""You are an Intent Classifier for a multi-agent AI system.

Your job is to analyze user queries and determine which specialized agent should handle the request.

AGENT CAPABILITIES:
{capabilities}

CLASSIFICATION RULES:
1. If user wants to create/write/save/code → "coder"
2. If user mentions planning, strategy, complex tasks → "planner"
3. If user mentions review, check, validate logic → "critic"
4. If user mentions test, run, execute, verify → "tester"
5. If user mentions final check, summary, review → "reviewer"
6. If it's a general question without coding → "general"
7. If you cannot determine intent with high confidence → "unknown"

Return JSON with:
- intent: one of the agent types above
- confidence: float between 0.0 and 1.0
- reasoning: brief explanation of your decision

Be precise. Only classify intent, DO NOT respond to the user."""

    def classify(
        self, user_input: str, conversation_history: Optional[List[str]] = None
    ) -> UserIntent:
        """Classify user intent and return routing decision.

        Parameters
        ----------
        user_input : str
            The user's current message.
        conversation_history : Optional[List[str]]
            Previous conversation turns for context.

        Returns
        -------
        UserIntent
            Dictionary with intent, confidence, and reasoning.
        """
        messages = [SystemMessage(content=self._build_system_prompt())]

        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 turns for context
                messages.append(HumanMessage(content=msg))

        messages.append(HumanMessage(content=user_input))

        try:
            response = self._model.invoke(messages)
            result = self._parse_response(response.content)

            if (
                result["confidence"] < self.config.confidence_threshold
                and self.config.enable_fallback
            ):
                return UserIntent(
                    intent="unknown",
                    confidence=result["confidence"],
                    reasoning=f"Low confidence ({result['confidence']} below threshold. Reasoning: {result['reasoning']}",
                )

            return result
        except Exception as e:
            return UserIntent(
                intent="general",
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}",
            )

    def _parse_response(self, response: str) -> UserIntent:
        """Parse LLM response into UserIntent structure."""
        import json
        import re

        try:
            if "```json" in response:
                json_str = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
                if json_str:
                    response = json_str.group(1)
            elif "```" in response:
                json_str = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
                if json_str:
                    response = json_str.group(1)

            parsed = json.loads(response)
            return UserIntent(
                intent=parsed.get("intent", "unknown"),
                confidence=float(parsed.get("confidence", 0.5)),
                reasoning=parsed.get("reasoning", "No reasoning provided"),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return UserIntent(
                intent="unknown",
                confidence=0.0,
                reasoning=f"Failed to parse response: {str(e)}",
            )

    def get_agent_for_intent(
        self, user_input: str, conversation_history: Optional[List[str]] = None
    ) -> str:
        """Get the target agent name for a given user input.

        Parameters
        ----------
        user_input : str
            The user's message.
        conversation_history : Optional[List[str]]
            Optional conversation context.

        Returns
        -------
        str
            Name of the agent to route to.
        """
        intent_result = self.classify(user_input, conversation_history)

        if intent_result["intent"] == "unknown":
            return "general"

        return intent_result["intent"]

    def update_capabilities(self, agent_name: str, description: str) -> None:
        """Update agent capabilities in the classifier.

        Parameters
        ----------
        agent_name : str
            Name of the agent.
        description : str
            New description of agent capabilities.
        """
        self._agent_capabilities[agent_name] = description


# Singleton instance for easy import
_classifier: Optional[IntentClassifier] = None


def get_classifier(config: Optional[IntentClassifierConfig] = None) -> IntentClassifier:
    """Get or create the singleton intent classifier instance.

    Parameters
    ----------
    config : Optional[IntentClassifierConfig]
        Configuration for the classifier.

    Returns
    -------
    IntentClassifier
        The classifier instance.
    """
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier(config)
    return _classifier
