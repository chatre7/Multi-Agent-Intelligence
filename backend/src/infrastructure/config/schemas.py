"""
JSON Schemas for YAML configuration documents.

These schemas are intentionally minimal for the MVP and can be extended over time.
"""

from __future__ import annotations

DOMAIN_SCHEMA: dict = {
    "type": "object",
    "required": ["id", "name", "description", "agents", "default_agent"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "agents": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "default_agent": {"type": "string", "minLength": 1},
        "workflow_type": {"type": "string"},
        "max_iterations": {"type": "integer", "minimum": 1},
        "routing_rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["keywords", "agent"],
                "properties": {
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "agent": {"type": "string"},
                    "priority": {"type": "integer"},
                },
                "additionalProperties": True,
            },
        },
        "fallback_agent": {"type": "string"},
        "allowed_roles": {"type": "array", "items": {"type": "string"}},
        "version": {"type": "string"},
        "is_active": {"type": "boolean"},
        "metadata": {"type": "object"},
    },
    "additionalProperties": True,
}

AGENT_SCHEMA: dict = {
    "type": "object",
    "required": [
        "id",
        "name",
        "domain_id",
        "description",
        "version",
        "state",
        "system_prompt",
        "capabilities",
        "tools",
        "model_name",
    ],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "domain_id": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "state": {"type": "string"},
        "system_prompt": {"type": "string"},
        "capabilities": {"type": "array", "items": {"type": "string"}},
        "tools": {"type": "array", "items": {"type": "string"}},
        "model_name": {"type": "string", "minLength": 1},
        "temperature": {"type": "number", "minimum": 0},
        "max_tokens": {"type": "integer", "minimum": 1},
        "timeout_seconds": {"type": "number", "minimum": 1},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "skills": {"type": "array", "items": {"type": "string"}},
        "priority": {"type": "integer"},
        "author": {"type": "string"},
        "metadata": {"type": "object"},
    },
    "additionalProperties": True,
}

TOOL_SCHEMA: dict = {
    "type": "object",
    "required": ["id", "name", "description", "parameters_schema", "returns_schema"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "parameters_schema": {"type": "object"},
        "returns_schema": {"type": "object"},
        "handler_path": {"type": "string"},
        "timeout_seconds": {"type": "number", "minimum": 1},
        "max_retries": {"type": "integer", "minimum": 0},
        "requires_approval": {"type": "boolean"},
        "allowed_roles": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "domain": {"type": ["string", "null"]},
        "version": {"type": "string"},
        "is_async": {"type": "boolean"},
        "metadata": {"type": "object"},
    },
    "additionalProperties": True,
}
