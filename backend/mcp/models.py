from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


MCPToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: MCPToolHandler
