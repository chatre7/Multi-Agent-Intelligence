"""Prometheus metrics (MVP)."""

from __future__ import annotations

from prometheus_client import Counter

CHAT_MESSAGES_TOTAL = Counter(
    "multi_agent_chat_messages_total",
    "Total number of chat messages received.",
)

TOOL_RUNS_REQUESTED_TOTAL = Counter(
    "multi_agent_tool_runs_requested_total",
    "Total number of tool runs requested.",
)

TOOL_RUNS_APPROVED_TOTAL = Counter(
    "multi_agent_tool_runs_approved_total",
    "Total number of tool runs approved.",
)

TOOL_RUNS_REJECTED_TOTAL = Counter(
    "multi_agent_tool_runs_rejected_total",
    "Total number of tool runs rejected.",
)

TOOL_RUNS_EXECUTED_TOTAL = Counter(
    "multi_agent_tool_runs_executed_total",
    "Total number of tool runs executed.",
)
