from __future__ import annotations

import logging
from typing import Any

from backend.mcp.models import MCPTool


logger = logging.getLogger(__name__)


class MCPToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool
        logger.info("MCP tool registered: %s", tool.name)

    def get(self, tool_name: str) -> MCPTool | None:
        return self._tools.get(tool_name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]
