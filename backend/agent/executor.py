from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.agent.memory import MemoryStore
from backend.agent.planner import AgentPlanner
from backend.tools.db import save_to_db
from backend.tools.drive import upload_to_drive
from backend.tools.image import extract_image
from backend.tools.pdf import extract_pdf
from backend.tools.search import web_search
from backend.utils.config import Settings
from backend.utils.gemini import (
    VertexConfigurationError,
    VertexGeminiClient,
    VertexGenerationError,
)


logger = logging.getLogger(__name__)


class ToolExecutionError(RuntimeError):
    pass


class AgentExecutor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.gemini = VertexGeminiClient(settings)
        self.planner = AgentPlanner(self.gemini)
        self.memory = MemoryStore(settings.memory_db_path)
        self.tool_registry: dict[str, Callable[..., Any]] = {
            "web_search": self._tool_web_search,
            "extract_pdf": self._tool_extract_pdf,
            "extract_image": self._tool_extract_image,
            "save_to_db": self._tool_save_to_db,
            "upload_to_drive": self._tool_upload_to_drive,
        }

    def run(
        self,
        user_input: str,
        preferred_output: str | None = None,
        file_context: list[dict[str, Any]] | None = None,
        upload_results_to_drive: bool = False,
        initial_tool_calls: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        normalized_files = self._normalize_file_context(file_context)
        state = self._initialize_state(normalized_files)
        self._record_step(state, "Planning research")

        tool_traces: list[dict[str, Any]] = []
        for trace in initial_tool_calls or []:
            tool_traces.append(trace)
            self._apply_tool_trace(
                tool_name=str(trace.get("tool") or "unknown"),
                trace=trace,
                state=state,
            )

        extracted_context = state["extracted_text"].strip()
        plan = self.planner.plan(
            user_input=user_input,
            context_text=extracted_context,
            preferred_output=preferred_output,
            upload_requested=upload_results_to_drive,
        )

        deferred_steps: list[dict[str, Any]] = []
        for step in plan.get("workflow", []):
            if not isinstance(step, dict):
                continue

            tool_name = str(step.get("tool") or "none").strip()
            if tool_name == "none":
                continue
            if tool_name in {"save_to_db", "upload_to_drive"}:
                deferred_steps.append(step)
                continue

            trace = self._execute_workflow_step(
                step=step,
                state=state,
                plan=plan,
                user_input=user_input,
            )
            tool_traces.append(trace)

        sources = self._attach_source_reference_ids(
            self._deduplicate_sources(state["sources"])
        )

        self._record_step(state, "Generating content")
        generated_content = self._generate_content(
            user_input=user_input,
            plan=plan,
            sources=sources,
            file_context=normalized_files,
            state=state,
        )

        memory_info = self.memory.save_run(
            topic=plan["topic"],
            input_prompt=user_input,
            output_type=plan["output_type"],
            content=generated_content,
            plan=plan,
            sources=sources,
        )

        output_path = self._write_output_file(
            topic=plan["topic"],
            output_type=plan["output_type"],
            content=generated_content,
        )
        state["output_file"] = str(output_path)

        save_executed = False
        upload_executed = False
        for step in deferred_steps:
            trace = self._execute_workflow_step(
                step=step,
                state=state,
                plan=plan,
                user_input=user_input,
                generated_content=generated_content,
                output_path=output_path,
                memory_info=memory_info,
                upload_requested=upload_results_to_drive,
            )
            tool_traces.append(trace)

            tool_name = str(step.get("tool") or "").strip()
            if tool_name == "save_to_db" and trace.get("status") == "success":
                save_executed = True
            if tool_name == "upload_to_drive" and trace.get("status") == "success":
                upload_executed = True

        if not save_executed:
            auto_save_trace = self._execute_workflow_step(
                step={
                    "action": "Saving run metadata",
                    "tool": "save_to_db",
                    "input": {},
                },
                state=state,
                plan=plan,
                user_input=user_input,
                generated_content=generated_content,
                output_path=output_path,
                memory_info=memory_info,
            )
            tool_traces.append(auto_save_trace)

        if upload_results_to_drive and not upload_executed:
            auto_upload_trace = self._execute_workflow_step(
                step={
                    "action": "Uploading generated file to Google Drive",
                    "tool": "upload_to_drive",
                    "input": {"file_path": str(output_path)},
                },
                state=state,
                plan=plan,
                user_input=user_input,
                generated_content=generated_content,
                output_path=output_path,
                memory_info=memory_info,
                upload_requested=True,
            )
            tool_traces.append(auto_upload_trace)

        if upload_results_to_drive and not state["drive_link"]:
            raise ToolExecutionError(
                state.get("last_upload_error")
                or "Google Drive upload failed before a shareable link was produced."
            )

        if state["drive_link"]:
            self.memory.update_drive_link(memory_info["output_id"], state["drive_link"])

        return {
            "plan": plan.get("workflow", []),
            "sources": sources,
            "output": generated_content,
            "drive_link": state["drive_link"],
            "memory_id": str(memory_info["output_id"]),
            "steps": state["steps"],
        }

    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        handler = self.tool_registry.get(tool_name)
        if not handler:
            return {
                "tool": tool_name,
                "status": "error",
                "input": tool_input,
                "error": f"Tool '{tool_name}' is not registered.",
            }

        try:
            output = handler(**tool_input)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Tool execution failed: %s", tool_name)
            return {
                "tool": tool_name,
                "status": "error",
                "input": tool_input,
                "error": str(exc),
            }

        if isinstance(output, dict) and output.get("status") == "error":
            return {
                "tool": tool_name,
                "status": "error",
                "input": tool_input,
                "error": output.get("error", "Tool returned an error."),
                "output": output,
            }

        return {
            "tool": tool_name,
            "status": "success",
            "input": tool_input,
            "output": output,
        }

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.memory.get_history(limit=limit)

    def _tool_web_search(self, query: str, max_results: int = 5) -> dict[str, Any]:
        return web_search(query=query, max_results=max_results)

    def _tool_extract_pdf(self, file_path: str) -> dict[str, Any]:
        return extract_pdf(file_path=file_path)

    def _tool_extract_image(self, file_path: str) -> dict[str, Any]:
        return extract_image(file_path=file_path)

    def _tool_save_to_db(self, data: dict[str, Any]) -> dict[str, Any]:
        return save_to_db(data=data, db_path=self.settings.tool_db_path)

    def _tool_upload_to_drive(self, file_path: str) -> dict[str, Any]:
        return upload_to_drive(file_path=file_path, settings=self.settings)

    @staticmethod
    def _initialize_state(file_context: list[dict[str, Any]]) -> dict[str, Any]:
        extracted_text = "\n\n".join(
            item.get("text", "").strip()
            for item in file_context
            if isinstance(item, dict) and item.get("text")
        ).strip()
        return {
            "sources": [],
            "extracted_text": extracted_text,
            "files": file_context,
            "logs": [],
            "steps": [],
            "drive_link": None,
            "last_upload_error": None,
            "output_file": None,
        }

    @staticmethod
    def _normalize_file_context(
        file_context: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for item in file_context or []:
            if not isinstance(item, dict):
                continue
            items.append(
                {
                    "file_name": item.get("file_name", "uploaded_file"),
                    "file_type": item.get("file_type", "unknown"),
                    "file_path": item.get("file_path"),
                    "text": item.get("text", ""),
                }
            )
        return items

    def _execute_workflow_step(
        self,
        step: dict[str, Any],
        state: dict[str, Any],
        plan: dict[str, Any],
        user_input: str,
        generated_content: str | None = None,
        output_path: Path | None = None,
        memory_info: dict[str, Any] | None = None,
        upload_requested: bool = False,
    ) -> dict[str, Any]:
        tool_name = str(step.get("tool") or "none").strip()
        action = str(step.get("action") or f"Running {tool_name}").strip()
        self._record_step(state, action)

        if tool_name == "upload_to_drive" and not upload_requested:
            return {
                "tool": tool_name,
                "status": "skipped",
                "input": {},
                "error": "Drive upload was not requested for this run.",
            }

        tool_input = self._resolve_tool_input(
            tool_name=tool_name,
            raw_input=step.get("input"),
            state=state,
            plan=plan,
            user_input=user_input,
            generated_content=generated_content,
            output_path=output_path,
            memory_info=memory_info,
        )

        if tool_name in {"extract_pdf", "extract_image"} and not tool_input.get("file_path"):
            trace = {
                "tool": tool_name,
                "status": "error",
                "input": tool_input,
                "error": f"{tool_name} requires a file_path.",
            }
            self._apply_tool_trace(tool_name, trace, state)
            return trace

        if tool_name == "upload_to_drive" and not tool_input.get("file_path"):
            trace = {
                "tool": tool_name,
                "status": "error",
                "input": tool_input,
                "error": "upload_to_drive requires a generated file path.",
            }
            self._apply_tool_trace(tool_name, trace, state)
            return trace

        trace = self.execute_tool(tool_name, tool_input)
        self._apply_tool_trace(tool_name, trace, state)
        return trace

    def _resolve_tool_input(
        self,
        tool_name: str,
        raw_input: Any,
        state: dict[str, Any],
        plan: dict[str, Any],
        user_input: str,
        generated_content: str | None = None,
        output_path: Path | None = None,
        memory_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        tool_input = raw_input if isinstance(raw_input, dict) else {}
        resolved = dict(tool_input)

        if tool_name == "web_search":
            if not resolved.get("query"):
                fallback_query = plan.get("search_queries", [plan.get("topic", user_input)])
                resolved["query"] = str(fallback_query[0])
            resolved["max_results"] = int(resolved.get("max_results") or 5)
            return resolved

        if tool_name in {"extract_pdf", "extract_image"}:
            if not resolved.get("file_path"):
                for file_item in state.get("files", []):
                    if not isinstance(file_item, dict):
                        continue
                    file_type = str(file_item.get("file_type") or "").lower()
                    if tool_name == "extract_pdf" and file_type == "pdf":
                        resolved["file_path"] = file_item.get("file_path")
                        break
                    if tool_name == "extract_image" and file_type == "image":
                        resolved["file_path"] = file_item.get("file_path")
                        break
            return resolved

        if tool_name == "save_to_db":
            payload = resolved.get("data")
            if not isinstance(payload, dict):
                payload = {}
            payload.setdefault("event_type", "agent_run")
            payload.setdefault("topic", plan.get("topic"))
            payload.setdefault("input_prompt", user_input)
            payload.setdefault("output_type", plan.get("output_type"))
            payload.setdefault("source_count", len(state.get("sources", [])))
            payload.setdefault("has_file_context", bool(state.get("files")))
            payload.setdefault("memory_id", (memory_info or {}).get("output_id"))
            payload.setdefault("output_file", str(output_path) if output_path else None)
            payload.setdefault("drive_link", state.get("drive_link"))
            payload.setdefault("generated_preview", (generated_content or "")[:500])
            payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            resolved["data"] = payload
            return resolved

        if tool_name == "upload_to_drive":
            if not resolved.get("file_path") and output_path is not None:
                resolved["file_path"] = str(output_path)
            return resolved

        return resolved

    def _apply_tool_trace(
        self,
        tool_name: str,
        trace: dict[str, Any],
        state: dict[str, Any],
    ) -> None:
        status = str(trace.get("status") or "unknown")
        if status == "error":
            message = trace.get("error", f"{tool_name} failed.")
            state["logs"].append(str(message))
            if tool_name == "upload_to_drive":
                state["last_upload_error"] = str(message)
            return
        if status == "skipped":
            state["logs"].append(str(trace.get("error", f"{tool_name} skipped.")))
            return

        output = trace.get("output")
        if tool_name == "web_search" and isinstance(output, dict):
            results = output.get("results", [])
            if isinstance(results, list):
                state["sources"].extend(results)
        elif tool_name in {"extract_pdf", "extract_image"} and isinstance(output, dict):
            extracted_text = str(output.get("text") or "").strip()
            if extracted_text:
                current = state.get("extracted_text", "")
                state["extracted_text"] = (
                    f"{current}\n\n{extracted_text}".strip() if current else extracted_text
                )
        elif tool_name == "upload_to_drive" and isinstance(output, dict):
            drive_link = output.get("link")
            if drive_link:
                state["drive_link"] = str(drive_link)

    @staticmethod
    def _record_step(state: dict[str, Any], message: str) -> None:
        steps = state.setdefault("steps", [])
        if not isinstance(steps, list):
            return
        if not steps or steps[-1] != message:
            steps.append(message)

    def _generate_content(
        self,
        user_input: str,
        plan: dict[str, Any],
        sources: list[dict[str, Any]],
        file_context: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> str:
        self.gemini.ensure_available()

        source_block = "\n".join(
            [
                f"[{source['ref_id']}] {source['title']} | {source['url']}\n{source['snippet']}"
                for source in sources
            ]
        )

        file_context_block = "\n\n".join(
            [
                f"File: {item.get('file_name', 'uploaded_file')} ({item.get('file_type', 'unknown')})\n"
                f"Extracted text:\n{(item.get('text') or '')[:3500]}"
                for item in file_context
                if isinstance(item, dict)
            ]
        )

        format_instruction = self._output_format_instruction(plan.get("output_type", "summary"))
        planning_block = "\n".join(
            [
                f"Topic: {plan.get('topic')}",
                f"Output type: {plan.get('output_type')}",
                f"Sections: {', '.join(plan.get('sections', []))}",
                f"Completed steps: {', '.join(state.get('steps', []))}",
            ]
        )

        prompt = f"""
You are an autonomous research assistant.
Use the plan, sources, and extracted file content to produce the final response.

{format_instruction}

User request:
{user_input}

Agent plan:
{planning_block}

Web sources (use references like [S1], [S2] inline when relevant):
{source_block or "No external web sources were collected."}

Uploaded file context:
{file_context_block or "No uploaded files."}

Requirements:
1. Be concrete and useful.
2. Ground factual claims in the provided sources when available.
3. If source coverage is weak, say so briefly instead of inventing citations.
4. End with a "References" section listing the cited [S#] entries.
"""

        return self.gemini.generate_text(
            prompt=prompt,
            temperature=0.25,
            max_output_tokens=4096,
        ).strip()

    @staticmethod
    def _output_format_instruction(output_type: str) -> str:
        if output_type == "research_paper":
            return (
                "Format as a mini research paper with clear headings: "
                "Abstract, Introduction, Approach, Findings, Conclusion."
            )
        if output_type == "speech":
            return "Format as a speech script with opening, body, and closing."
        if output_type == "notes":
            return "Format as concise notes with bullets and key points."
        if output_type == "project_plan":
            return "Format as a project plan with milestones, risks, and next actions."
        return "Format as an executive summary."

    @staticmethod
    def _deduplicate_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for source in sources:
            url = (source.get("url") or "").strip().lower()
            title = (source.get("title") or "").strip().lower()
            key = url or title
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(
                {
                    "title": source.get("title", "Untitled Source"),
                    "url": source.get("url", ""),
                    "snippet": source.get("snippet", ""),
                }
            )
        return unique[:8]

    @staticmethod
    def _attach_source_reference_ids(
        sources: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for index, source in enumerate(sources, start=1):
            output.append(
                {
                    "ref_id": f"S{index}",
                    "title": source.get("title", "Untitled Source"),
                    "url": source.get("url", ""),
                    "snippet": source.get("snippet", ""),
                }
            )
        return output

    def _write_output_file(self, topic: str, output_type: str, content: str) -> Path:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.strip().lower()).strip("_")
        if not slug:
            slug = "research_output"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{slug}_{output_type}_{timestamp}.md"
        target = self.settings.generated_dir / filename
        target.write_text(content, encoding="utf-8")
        return target
