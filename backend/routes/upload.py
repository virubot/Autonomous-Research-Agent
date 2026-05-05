from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.agent.executor import AgentExecutor, ToolExecutionError
from backend.utils.dependencies import get_executor
from backend.utils.gemini import VertexConfigurationError, VertexGenerationError


router = APIRouter(tags=["upload"])


def _safe_filename(filename: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "_", filename).strip("._")
    return clean[:120] or "upload.bin"


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    prompt: str | None = Form(default=None),
    output_type: str | None = Form(default=None),
    upload_to_drive: bool = Form(default=False),
    executor: AgentExecutor = Depends(get_executor),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    extension = Path(file.filename).suffix.lower()
    is_pdf = file.content_type == "application/pdf" or extension == ".pdf"
    is_image = (
        (file.content_type or "").startswith("image/")
        or extension in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
    )
    if not is_pdf and not is_image:
        raise HTTPException(status_code=400, detail="Only PDF or image files are supported.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{_safe_filename(file.filename)}"
    destination = executor.settings.upload_dir / safe_name
    destination.write_bytes(await file.read())

    extraction_tool = "extract_pdf" if is_pdf else "extract_image"
    extraction_trace = executor.execute_tool(extraction_tool, {"file_path": str(destination)})
    if extraction_trace.get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail=extraction_trace.get("error", "File extraction failed."),
        )

    extraction_output = extraction_trace.get("output", {})
    extracted_text = (extraction_output.get("text") or "").strip()
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from uploaded file.")

    stored_file = executor.memory.save_uploaded_file(
        filename=file.filename,
        file_type="pdf" if is_pdf else "image",
        file_path=str(destination),
        extracted_preview=extracted_text[:500],
    )

    user_prompt = (
        (prompt or "").strip()
        or "Analyze the uploaded file and produce a concise, useful response."
    )
    file_context = [
        {
            "file_name": file.filename,
            "file_type": "pdf" if is_pdf else "image",
            "file_path": str(destination),
            "text": extracted_text,
        }
    ]

    try:
        response = executor.run(
            user_input=user_prompt,
            preferred_output=output_type,
            file_context=file_context,
            upload_results_to_drive=upload_to_drive,
            initial_tool_calls=[extraction_trace],
        )
    except VertexConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VertexGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ToolExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    response["uploaded_file"] = {
        "id": stored_file["id"],
        "filename": file.filename,
        "stored_path": str(destination),
        "file_type": "pdf" if is_pdf else "image",
        "extracted_characters": len(extracted_text),
    }
    return response
