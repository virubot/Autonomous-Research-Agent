from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
from pathlib import Path

# Services
from backend.services.pipeline_service import run_pipeline
from backend.services.assistant_service import intelligent_assistant
from backend.services.pdf_storage_service import (
    LATEST_PDF_PATH,
    PROJECT_ROOT,
    get_latest_pdf,
    init_db,
    list_pdf_files,
    store_generated_pdf,
)


# ----------------------------
# APP INIT
# ----------------------------
app = FastAPI(title="AI Research Assistant")
init_db()


# ----------------------------
# CORS (VERY IMPORTANT 🔥)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development (later restrict)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# REQUEST MODELS
# ----------------------------
class TopicRequest(BaseModel):
    topic: str


class QueryRequest(BaseModel):
    query: str


# ----------------------------
# HEALTH CHECK
# ----------------------------
@app.get("/")
def home():
    return {"message": "Backend running 🚀"}


# ----------------------------
# GENERATE RESEARCH PAPER
# ----------------------------
@app.post("/generate")
def generate(request: TopicRequest):
    try:
        previous_pdf_mtime = LATEST_PDF_PATH.stat().st_mtime_ns if LATEST_PDF_PATH.exists() else None
        result = run_pipeline(request.topic)

        if not result:
            return {"error": "Failed to generate paper"}

        if "error" not in result:
            try:
                current_pdf_mtime = LATEST_PDF_PATH.stat().st_mtime_ns if LATEST_PDF_PATH.exists() else None
                if current_pdf_mtime is not None and current_pdf_mtime != previous_pdf_mtime:
                    store_generated_pdf(request.topic)
            except Exception as storage_error:
                print("PDF storage failed:", storage_error)

        return result

    except Exception as e:
        return {
            "error": "Paper generation failed",
            "details": str(e)
        }


# ----------------------------
# AI ASSISTANT (RAG + LLM 🔥)
# ----------------------------
@app.post("/assistant")
def assistant(request: QueryRequest):
    try:
        result = intelligent_assistant(request.query)

        if not result or "answer" not in result:
            return {"answer": "No useful research data found."}

        return result

    except Exception as e:
        return {
            "answer": "Something went wrong in assistant.",
            "error": str(e)
        }




@app.get("/download")
def download_pdf():
    latest_pdf = get_latest_pdf()

    if latest_pdf:
        latest_path = Path(latest_pdf["filepath"])
        if not latest_path.is_absolute():
            latest_path = PROJECT_ROOT / latest_path

        if latest_path.exists():
            return FileResponse(
                str(latest_path),
                media_type="application/pdf",
                filename="research_paper.pdf"
            )

    return FileResponse(
        "research_paper.pdf",
        media_type="application/pdf",
        filename="research_paper.pdf"
    )


@app.get("/pdfs")
def pdfs():
    return list_pdf_files()
