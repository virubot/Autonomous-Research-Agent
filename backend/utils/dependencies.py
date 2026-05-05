from __future__ import annotations

from fastapi import Request

from backend.agent.executor import AgentExecutor


def get_executor(request: Request) -> AgentExecutor:
    return request.app.state.executor
