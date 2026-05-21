from __future__ import annotations

import asyncio
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.agent.executor import AgentExecutor, ToolExecutionError
from backend.utils.dependencies import get_executor
from backend.utils.gemini import VertexConfigurationError, VertexGenerationError


OutputType = Literal["research_paper", "summary", "speech", "notes", "project_plan"]
ToolMode = Literal["direct", "mcp"]


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
    tool_mode: ToolMode = Field(default="direct")
    format_type: str = Field(default="ieee")
    page_length: str = Field(default="4-5")
    include_formulas: bool = Field(default=False)
    include_diagrams: bool = Field(default=False)


router = APIRouter(tags=["agent"])


@router.post("/generate")
async def generate(
    request: GenerateRequest,
    executor: AgentExecutor = Depends(get_executor),
) -> dict:
    user_input = (request.prompt or request.topic or "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Provide either 'prompt' or 'topic'.")

    try:
        return await asyncio.to_thread(
            executor.run,
            user_input,
            request.output_type,
            None,
            request.upload_to_drive,
            None,
            request.tool_mode,
            None,
            request.format_type,
            request.page_length,
            request.include_formulas,
            request.include_diagrams,
        )
    except VertexConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VertexGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ToolExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/generate/stream")
async def generate_stream(
    prompt: str = Query(..., min_length=1),
    output_type: OutputType | None = Query(default=None),
    upload_to_drive: bool = Query(default=False),
    tool_mode: ToolMode = Query(default="direct"),
    format_type: str = Query(default="ieee"),
    page_length: str = Query(default="4-5"),
    include_formulas: bool = Query(default=False),
    include_diagrams: bool = Query(default=False),
    executor: AgentExecutor = Depends(get_executor),
) -> StreamingResponse:
    queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def event_callback(event_type: str, payload: dict[str, object]) -> None:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            {"event": event_type, "data": payload},
        )

    async def run_executor() -> None:
        try:
            result = await asyncio.to_thread(
                executor.run,
                prompt.strip(),
                output_type,
                None,
                upload_to_drive,
                None,
                tool_mode,
                event_callback,
                format_type,
                page_length,
                include_formulas,
                include_diagrams,
            )
            await queue.put({"event": "completed", "data": result})
        except Exception as exc:
            await queue.put({"event": "error", "data": {"message": str(exc)}})
        finally:
            await queue.put({"event": "end", "data": {}})

    async def event_stream():
        task = asyncio.create_task(run_executor())
        try:
            while True:
                item = await queue.get()
                event_name = str(item["event"])
                payload = item["data"]
                if event_name == "end":
                    break
                chunk = f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"
                yield chunk.encode("utf-8")
        finally:
            await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/history")
async def history(
    limit: int = 20,
    executor: AgentExecutor = Depends(get_executor),
) -> dict:
    items = await asyncio.to_thread(executor.get_history, limit)
    return {"status": "success", "items": items}