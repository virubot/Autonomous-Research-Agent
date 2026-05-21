"""
Research Service providing the modular interface for research synthesis, planning, and content generation.
"""
from __future__ import annotations

from typing import Any, Callable

from backend.agent.executor import AgentExecutor
from backend.utils.config import get_settings


class ResearchService:
    def __init__(self, executor: AgentExecutor | None = None) -> None:
        self.settings = get_settings()
        if executor is not None:
            self.executor = executor
        else:
            from backend.mcp import MCPServer
            mcp_server = MCPServer(enabled=self.settings.mcp_enabled)
            self.executor = AgentExecutor(settings=self.settings, mcp_server=mcp_server)

    def run_research(
        self,
        prompt: str,
        output_type: str | None = None,
        file_path: str | None = None,
        upload_to_drive: bool = False,
        memory_id: str | None = None,
        tool_mode: str = "direct",
        event_callback: Callable[[str, dict[str, Any]], None] | None = None,
        format_type: str = "ieee",
        page_length: str = "4-5",
        include_formulas: bool = False,
        include_diagrams: bool = False,
    ) -> dict[str, Any]:
        """
        Execute the full research pipeline.
        """
        return self.executor.run(
            user_input=prompt,
            output_type=output_type,
            file_path=file_path,
            upload_to_drive=upload_to_drive,
            memory_id=memory_id,
            tool_mode=tool_mode,
            event_callback=event_callback,
            format_type=format_type,
            page_length=page_length,
            include_formulas=include_formulas,
            include_diagrams=include_diagrams,
        )
