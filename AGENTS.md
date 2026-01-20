# Agent Guidelines for Multi-Agent-Intelligence

## Build, Lint, and Test Commands

### Testing
```bash
# Run all tests
pytest

# Run a specific test file
pytest test_math_tools.py

# Run a specific test function
pytest test_math_tools.py::test_add

# Run tests with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Running the Application
```bash
# Run the main Streamlit app
streamlit run app.py

# Run individual Python scripts
python calculator.py
python circle_area.py
```

### Linting and Type Checking
```bash
# Install development dependencies first:
# pip install pytest pytest-cov ruff mypy

# Run ruff for fast linting
ruff check .

# Auto-fix with ruff
ruff check --fix .

# Run mypy for type checking
mypy .

# Format code with ruff
ruff format .
```

## Code Style Guidelines

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports third
- Group imports by category with blank lines between groups
- Use absolute imports for clarity

```python
import os
import sqlite3
from typing import Annotated, Sequence, TypedDict

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from planner_agent_team_v3 import app as agent_app
```

### Type Annotations
- Always use type hints for function parameters and return values
- Use `typing` module for complex types (Union, Optional, Literal, etc.)
- Use Annotated for metadata
- Define type aliases for reusable complex types

```python
from typing import Union, Optional

Number = Union[int, float]

def calculate(a: Number, b: Number) -> Number:
    return a + b

def get_user_id(user_id: Optional[int] = None) -> int:
    return user_id or 0
```

### Naming Conventions
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: single underscore prefix `_private`
- Module names: `snake_case`

```python
class MemoryManager:
    def __init__(self):
        self._private_var = 0
        self.MAX_RETRIES = 3

def process_data(input_data: str) -> dict:
    return {"result": input_data}
```

### Docstring Style
- Use Google/Numpy-style docstrings
- Include Parameters, Returns, and Raises sections where applicable
- Keep docstrings concise but informative
- Use triple double-quotes

```python
def circle_area(radius: float) -> float:
    """Calculate the area of a circle.

    Parameters
    ----------
    radius : float
        The radius of the circle. Must be a non-negative number.

    Returns
    -------
    float
        The area of the circle.

    Raises
    ------
    ValueError
        If radius is negative.
    """
    if radius < 0:
        raise ValueError("Radius must be non-negative")
    return math.pi * radius ** 2
```

### Error Handling
- Use specific exception types when catching
- Include descriptive error messages
- Don't silently swallow exceptions
- Use try/except for user input and external calls

```python
def save_file(filename: str, content: str) -> str:
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ File '{filename}' saved successfully."
    except IOError as e:
        return f"❌ Error saving file: {e}"
```

### String Formatting
- Use f-strings for string interpolation
- Use descriptive variable names in f-strings
- Format numbers and dates appropriately

```python
result = calculate(2, 3)
print(f"Calculation result: {result}")
print(f"{a} + {b} = {result}")
```

### Code Organization
- Use section comments with visual separators
- Group related functions together
- Keep functions focused and small
- Use `if __name__ == "__main__":` for script execution

```python
# ==========================================
# 1. CONFIGURATION
# ==========================================

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

if __name__ == "__main__":
    main()
```

### Testing Conventions
- Test files named `test_*.py`
- Use pytest fixtures when needed
- Use descriptive test names
- Use parametrize for similar tests

```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

### Agent-Specific Guidelines
- Define clear system prompts for each agent role
- Use consistent message types (HumanMessage, AIMessage, ToolMessage)
- Implement proper state management with AgentState
- Use tools with clear descriptions
- Include emoji indicators for visual clarity in logs
- Maintain thread_id for session persistence

### Database and Memory
- Use SqliteSaver for LangGraph checkpointing
- Store vector embeddings in `./agent_brain` directory
- Implement memory save/search tools for agents
- Handle database connections with proper error handling

### Agent Registry Pattern
- Implement AgentRegistry class for dynamic agent discovery
- Store agent metadata: capabilities, endpoints, version, status
- Support agent registration (registry-initiated or self-register)
- Provide lookup functions to identify agents for specific tasks
- Track agent health and operational metrics

```python
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Dict] = {}
    def register(self, name: str, description: str, version: str = "1.0"):
        self._agents[name] = {"desc": description, "version": version}
    def get_agents_for_task(self, task: str) -> List[str]:
        return [name for name, meta in self._agents.items() if task.lower() in meta["desc"].lower()]
```

### Operational Resilience
- Implement health checks for all agents (local and remote)
- Use retry strategies with exponential backoff
- Set up fallback mechanisms (switch models, cached responses)
- Monitor token consumption and enforce thresholds
- Log agent interactions for auditability
- Track performance metrics per agent

### Security
- Implement input validation and sanitization
- Use role-based access control for agents
- Enable prompt injection detection and prevention
- Log all agent interactions for audit trails
- Isolate sensitive data and model outputs
- Implement rate limiting and abuse detection
- Use environment variables for secrets/config

### Agent Lifecycle Management
- Version all agents and their metadata
- Implement state machine: dev → test → prod
- Seal production environments to prevent unintended changes
- Track upstream/downstream dependencies (e.g., vector DB changes)
- Use semantic versioning for agents
- Maintain backward compatibility when possible

### Architecture Patterns
- Choose modular monolith for simplicity (agents as modules)
- Choose microservices for independent deployment and scaling
- Implement agent-to-agent communication via standardized protocols
- Support both local and remote agents
- Use supervisor pattern for managing agent clusters
- Document architectural decision records (ADRs)

### General Best Practices
- Keep functions under 50 lines when possible
- Avoid deep nesting (max 3-4 levels)
- Use meaningful variable and function names
- Comment complex logic, not obvious code
- Remove commented-out code before committing
- Run lint and type checks before committing
