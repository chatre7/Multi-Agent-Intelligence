"""
Tool Entity.

Represents an executable tool that agents can use to perform actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import jsonschema


@dataclass
class Tool:
    """
    Tool Entity - represents an executable tool.

    Tools are actions that agents can invoke to interact with external
    systems, files, APIs, etc. Each tool has a defined interface
    (parameters and return schema) and security settings.

    Attributes:
        id: Unique identifier for the tool.
        name: Human-readable name.
        description: Description of what the tool does.
        parameters_schema: JSON Schema for input parameters.
        returns_schema: JSON Schema for return value.
        handler_path: Python module path to the handler function.
        timeout_seconds: Timeout for tool execution.
        max_retries: Maximum retry attempts on failure.
        requires_approval: Whether tool needs human approval before execution.
        allowed_roles: User roles allowed to use this tool.
        tags: Categorization tags.
        domain: Optional domain this tool belongs to.
        version: Tool version.
        created_at: When the tool was created.
        is_async: Whether the tool runs asynchronously.
        metadata: Additional metadata.
    """

    # Required fields
    id: str
    name: str
    description: str
    parameters_schema: dict[str, Any]
    returns_schema: dict[str, Any]
    handler_path: str

    # Optional fields with defaults
    timeout_seconds: float = 30.0
    max_retries: int = 3
    requires_approval: bool = False
    allowed_roles: list[str] = field(default_factory=lambda: ["developer", "admin"])
    tags: list[str] = field(default_factory=list)
    domain: str | None = None
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_async: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_role_allowed(self, role: str) -> bool:
        """
        Check if a role is allowed to use this tool.

        Args:
            role: The user role to check.

        Returns:
            True if role is allowed.
        """
        return role.lower() in {r.lower() for r in self.allowed_roles}

    def has_tag(self, tag: str) -> bool:
        """
        Check if tool has a specific tag.

        Args:
            tag: The tag to check.

        Returns:
            True if tool has the tag.
        """
        return tag.lower() in {t.lower() for t in self.tags}

    def validate_parameters(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate parameters against the schema.

        Args:
            params: Parameters to validate.

        Returns:
            Tuple of (is_valid, list of error messages).
        """
        errors = []

        try:
            jsonschema.validate(instance=params, schema=self.parameters_schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(str(e.message))
            return False, errors
        except jsonschema.SchemaError as e:
            errors.append(f"Invalid schema: {e.message}")
            return False, errors

    def get_required_parameters(self) -> list[str]:
        """
        Get list of required parameter names.

        Returns:
            List of required parameter names.
        """
        return self.parameters_schema.get("required", [])

    def get_parameter_info(self) -> dict[str, dict[str, Any]]:
        """
        Get information about all parameters.

        Returns:
            Dictionary mapping parameter names to their properties.
        """
        properties = self.parameters_schema.get("properties", {})
        required = set(self.get_required_parameters())

        result = {}
        for name, props in properties.items():
            result[name] = {
                "type": props.get("type", "any"),
                "description": props.get("description", ""),
                "required": name in required,
                "default": props.get("default"),
            }

        return result

    def to_langchain_tool_schema(self) -> dict[str, Any]:
        """
        Convert to LangChain tool schema format.

        Returns:
            Dictionary in LangChain tool schema format.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema,
        }

    def to_openai_function_schema(self) -> dict[str, Any]:
        """
        Convert to OpenAI function calling schema format.

        Returns:
            Dictionary in OpenAI function schema format.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize tool to dictionary.

        Returns:
            Dictionary representation of the tool.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters_schema": self.parameters_schema.copy(),
            "returns_schema": self.returns_schema.copy(),
            "handler_path": self.handler_path,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "requires_approval": self.requires_approval,
            "allowed_roles": self.allowed_roles.copy(),
            "tags": self.tags.copy(),
            "domain": self.domain,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "is_async": self.is_async,
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tool:
        """
        Deserialize tool from dictionary.

        Args:
            data: Dictionary containing tool data.

        Returns:
            Tool instance.
        """
        # Parse timestamp
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(UTC)

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            parameters_schema=data.get("parameters_schema", {"type": "object"}),
            returns_schema=data.get("returns_schema", {"type": "object"}),
            handler_path=data.get("handler_path", ""),
            timeout_seconds=data.get("timeout_seconds", 30.0),
            max_retries=data.get("max_retries", 3),
            requires_approval=data.get("requires_approval", False),
            allowed_roles=data.get("allowed_roles", ["developer", "admin"]),
            tags=data.get("tags", []),
            domain=data.get("domain"),
            version=data.get("version", "1.0.0"),
            created_at=created_at,
            is_async=data.get("is_async", False),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """String representation."""
        approval = " [approval required]" if self.requires_approval else ""
        return f"Tool({self.id}: {self.name}{approval})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Tool(id='{self.id}', name='{self.name}', "
            f"requires_approval={self.requires_approval})"
        )
