"""
YAML configuration loader.

Loads domains, agents, and tools from YAML files on disk into domain entities.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig, RoutingRule
from src.domain.entities.tool import Tool
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion

from .bundle import ConfigBundle
from .exceptions import ConfigError, ConfigValidationError
from .schemas import AGENT_SCHEMA, DOMAIN_SCHEMA, TOOL_SCHEMA


def _iter_yaml_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.yml"):
        if path.is_file():
            yield path
    for path in root.rglob("*.yaml"):
        if path.is_file():
            yield path


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Failed to read config file: {path}") from exc

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file: {path}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigValidationError(
            "YAML document must be a mapping/object at the top level.",
            path=str(path),
        )
    return data


def _validate_schema(
    data: Mapping[str, Any], schema: Mapping[str, Any], *, path: Path
) -> None:
    try:
        jsonschema.validate(instance=dict(data), schema=dict(schema))
    except jsonschema.ValidationError as exc:
        raise ConfigValidationError(
            f"Schema validation failed: {exc.message}",
            path=str(path),
        ) from exc
    except jsonschema.SchemaError as exc:
        raise ConfigError(f"Internal schema error: {exc.message}") from exc


@dataclass(frozen=True)
class ConfigFileInfo:
    """A single config file's fingerprint material."""

    relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class ConfigSnapshot:
    """Snapshot of the current on-disk config set."""

    hash: str
    file_count: int
    generated_at: str
    files: list[ConfigFileInfo]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class YamlConfigLoader:
    """
    Loads YAML configs from a config root directory.

    Expected structure (MVP):
        configs/
          domains/*.yaml
          agents/**/*.yaml
          tools/*.yaml
    """

    config_root: Path

    @classmethod
    def from_default_backend_root(cls) -> YamlConfigLoader:
        """Create loader using `backend/configs` relative to this package."""
        env_root = Path(os.getenv("CONFIG_ROOT")) if os.getenv("CONFIG_ROOT") else None
        if env_root is not None:
            return cls(config_root=env_root)
        current_file = Path(__file__).resolve()
        backend_root = current_file.parents[3]
        return cls(config_root=backend_root / "configs")

    def load_bundle(self) -> ConfigBundle:
        """Load all configs into a single bundle."""
        domains = {domain.id: domain for domain in self.load_domains()}
        agents = {agent.id: agent for agent in self.load_agents()}
        tools = {tool.id: tool for tool in self.load_tools()}
        return ConfigBundle(domains=domains, agents=agents, tools=tools)

    def snapshot(self) -> ConfigSnapshot:
        """Compute a fingerprint snapshot of all YAML config files."""
        file_infos: list[ConfigFileInfo] = []
        for path in self._iter_all_config_paths():
            rel = str(path.relative_to(self.config_root)).replace("\\", "/")
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise ConfigError(f"Failed to read config file: {path}") from exc
            sha = hashlib.sha256(data).hexdigest()
            file_infos.append(
                ConfigFileInfo(
                    relative_path=rel,
                    sha256=sha,
                    size_bytes=len(data),
                )
            )

        file_infos.sort(key=lambda f: f.relative_path)
        material = "\n".join(
            f"{f.relative_path}:{f.sha256}:{f.size_bytes}" for f in file_infos
        )
        overall = _sha256_text(material)
        return ConfigSnapshot(
            hash=overall,
            file_count=len(file_infos),
            generated_at=datetime.now(UTC).isoformat(),
            files=file_infos,
        )

    def _iter_all_config_paths(self) -> Iterable[Path]:
        for folder in ("domains", "agents", "tools"):
            root = self.config_root / folder
            if root.exists():
                yield from _iter_yaml_files(root)

    def load_domains(self) -> list[DomainConfig]:
        """Load all domain configs."""
        domains_dir = self.config_root / "domains"
        if not domains_dir.exists():
            return []
        domains: list[DomainConfig] = []
        for path in _iter_yaml_files(domains_dir):
            data = _read_yaml(path)
            _validate_schema(data, DOMAIN_SCHEMA, path=path)
            domains.append(self._domain_from_dict(data))
        return domains

    def load_agents(self) -> list[Agent]:
        """Load all agent configs."""
        agents_dir = self.config_root / "agents"
        if not agents_dir.exists():
            return []
        agents: list[Agent] = []
        for path in _iter_yaml_files(agents_dir):
            data = _read_yaml(path)
            _validate_schema(data, AGENT_SCHEMA, path=path)
            agents.append(self._agent_from_dict(data))
        return agents

    def load_tools(self) -> list[Tool]:
        """Load all tool configs."""
        tools_dir = self.config_root / "tools"
        if not tools_dir.exists():
            return []
        tools: list[Tool] = []
        for path in _iter_yaml_files(tools_dir):
            data = _read_yaml(path)
            _validate_schema(data, TOOL_SCHEMA, path=path)
            tools.append(self._tool_from_dict(data))
        return tools

    def _domain_from_dict(self, data: dict[str, Any]) -> DomainConfig:
        routing_rules_raw = data.get("routing_rules", [])
        routing_rules: list[RoutingRule] = []
        for rule in routing_rules_raw:
            if isinstance(rule, RoutingRule):
                routing_rules.append(rule)
            elif isinstance(rule, dict):
                routing_rules.append(RoutingRule.from_dict(rule))
            else:
                raise ConfigValidationError(
                    "routing_rules items must be objects.",
                )

        return DomainConfig(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            agents=list(data.get("agents", [])),
            default_agent=data["default_agent"],
            workflow_type=data.get("workflow_type", "supervisor"),
            max_iterations=int(data.get("max_iterations", 10)),
            routing_rules=routing_rules,
            fallback_agent=data.get("fallback_agent", ""),
            allowed_roles=list(
                data.get("allowed_roles", ["user", "developer", "admin"])
            ),
            version=data.get("version", "1.0.0"),
            is_active=bool(data.get("is_active", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def _agent_from_dict(self, data: dict[str, Any]) -> Agent:
        return Agent(
            id=data["id"],
            name=data["name"],
            domain_id=data["domain_id"],
            description=data.get("description", ""),
            version=SemanticVersion.from_string(data["version"]),
            state=AgentState.from_string(data["state"]),
            system_prompt=data.get("system_prompt", ""),
            capabilities=list(data.get("capabilities", [])),
            tools=list(data.get("tools", [])),
            model_name=data["model_name"],
            temperature=float(data.get("temperature", 0.0)),
            max_tokens=int(data.get("max_tokens", 4096)),
            timeout_seconds=float(data.get("timeout_seconds", 120.0)),
            keywords=list(data.get("keywords", [])),
            priority=int(data.get("priority", 0)),
            author=data.get("author", "system"),
        )

    def _tool_from_dict(self, data: dict[str, Any]) -> Tool:
        handler_path = data.get("handler_path", "")
        if not handler_path:
            handler_path = "src.infrastructure.tools.noop.noop"

        return Tool(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            parameters_schema=dict(data.get("parameters_schema", {"type": "object"})),
            returns_schema=dict(data.get("returns_schema", {"type": "object"})),
            handler_path=handler_path,
            timeout_seconds=float(data.get("timeout_seconds", 30.0)),
            max_retries=int(data.get("max_retries", 3)),
            requires_approval=bool(data.get("requires_approval", False)),
            allowed_roles=list(data.get("allowed_roles", ["developer", "admin"])),
            tags=list(data.get("tags", [])),
            domain=data.get("domain"),
            version=data.get("version", "1.0.0"),
            is_async=bool(data.get("is_async", False)),
            metadata=dict(data.get("metadata", {})),
        )
