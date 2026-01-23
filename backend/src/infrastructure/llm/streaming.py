"""Streaming LLM adapters.

This module provides a small abstraction for token streaming. The backend can run in
`deterministic` mode (tests/offline) or use a real provider like `openai`.
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from collections.abc import Iterator


def _split_tokens(text: str) -> list[str]:
    parts = re.split(r"(\s+)", text)
    return [p for p in parts if p]


class StreamingLLM(ABC):
    """Minimal interface for token streaming."""

    @abstractmethod
    def stream_chat(
        self,
        *,
        model: str,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Iterator[str]:
        """Yield content chunks for a chat completion."""


class DeterministicStreamingLLM(StreamingLLM):
    """Offline deterministic streamer used for tests."""

    def stream_chat(
        self,
        *,
        model: str,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Iterator[str]:
        _ = (system_prompt, temperature, max_tokens)
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )
        text = f"LLM({model}): {last_user}".strip()
        yield from _split_tokens(text)


class OpenAIStreamingLLM(StreamingLLM):
    """OpenAI chat.completions streaming adapter."""

    def __init__(self) -> None:
        from openai import OpenAI  # type: ignore[import-not-found]

        base_url = os.getenv("OPENAI_BASE_URL")
        self._client = OpenAI(base_url=base_url) if base_url else OpenAI()

    def stream_chat(
        self,
        *,
        model: str,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Iterator[str]:
        request_messages: list[dict[str, str]] = []
        if system_prompt:
            request_messages.append({"role": "system", "content": system_prompt})
        request_messages.extend(messages)

        print(f"[DEBUG] OpenAI Stream Request: model={model}, base_url={self._client.base_url}")
        try:
            stream = self._client.chat.completions.create(
                model=model,
                messages=request_messages,
                temperature=float(temperature),
                max_tokens=int(max_tokens),
                stream=True,
            )
            for event in stream:
                try:
                    delta = event.choices[0].delta
                    content = getattr(delta, "content", None)
                    if content:
                        yield content
                except Exception as e:
                     print(f"[DEBUG] OpenAI Stream Event Error: {e}")
        except Exception as e:
            print(f"[DEBUG] OpenAI Client Error: {e}")
            yield ""


def llm_from_env() -> StreamingLLM:
    """Create a streaming LLM adapter from environment settings."""

    provider = (os.getenv("LLM_PROVIDER", "deterministic") or "deterministic").lower()
    if provider == "deterministic":
        return DeterministicStreamingLLM()
    if provider == "openai":
        return OpenAIStreamingLLM()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
