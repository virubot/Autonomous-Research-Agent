from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.agent.executor import AgentExecutor, ToolExecutionError
from backend.utils.dependencies import get_executor
from backend.utils.gemini import VertexConfigurationError, VertexGenerationError


OutputType = Literal["research_paper", "summary", "speech", "notes", "project_plan"]


class GenerateRequest(BaseModel):
    prompt: str | None = Field(default=None, description="Primary user request.")
    topic: str | None = Field(default=None, description="Alias for prompt.")
    output_type: OutputType | None = Field(
        default=None,
        description="Optional desired output format.",
    )
    upload_to_drive: bool = Field(
        default=False,
        description="If true, generated output is uploaded to Google Drive.",
    )


router = APIRouter(tags=["agent"])


@router.post("/generate")
def generate(
    request: GenerateRequest,
    executor: AgentExecutor = Depends(get_executor),
) -> dict:
    user_input = (request.prompt or request.topic or "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Provide either 'prompt' or 'topic'.")

    try:
        return executor.run(
            user_input=user_input,
            preferred_output=request.output_type,
            upload_results_to_drive=request.upload_to_drive,
        )
    except VertexConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VertexGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ToolExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/history")
def history(
    limit: int = 20,
    executor: AgentExecutor = Depends(get_executor),
) -> dict:
    return {
        "status": "success",
        "items": executor.get_history(limit=limit),
    }
