from __future__ import annotations

from typing import Any

from backend.mcp.registry import MCPToolRegistry


class MCPDispatchError(RuntimeError):
    pass


class MCPDispatcher:
    def __init__(self, registry: MCPToolRegistry) -> None:
        self.registry = registry

    def dispatch(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        tool = self.registry.get(tool_name)
        if not tool:
            raise MCPDispatchError(f"MCP tool '{tool_name}' is not registered.")
        return tool.handler(payload)
