from __future__ import annotations

import logging
from typing import Any

from backend.mcp.dispatcher import MCPDispatchError, MCPDispatcher
from backend.mcp.models import MCPTool
from backend.mcp.registry import MCPToolRegistry


logger = logging.getLogger(__name__)


class MCPServer:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.started = False
        self.registry = MCPToolRegistry()
        self.dispatcher = MCPDispatcher(self.registry)

    def start(self) -> None:
        self.started = self.enabled
        if self.started:
            logger.info("MCP server started with %s registered tools.", len(self.registry.list_tools()))
        else:
            logger.warning("MCP server is disabled by configuration.")

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler,
    ) -> None:
        self.registry.register(
            MCPTool(
                name=name,
                description=description,
                input_schema=input_schema,
                handler=handler,
            )
        )

    def execute(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.started:
            raise MCPDispatchError("MCP server is not started.")
        return self.dispatcher.dispatch(tool_name, payload)

    def health(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "started": self.started,
            "tool_count": len(self.registry.list_tools()),
            "tools": [tool["name"] for tool in self.registry.list_tools()],
        }
