from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.agent.memory import MemoryStore
from backend.agent.planner import AgentPlanner
from backend.mcp import MCPDispatchError, MCPServer
from backend.tools.drive import upload_to_drive
from backend.tools.image import extract_image
from backend.tools.pdf import extract_pdf
from backend.tools.search import web_search
from backend.utils.config import Settings
from backend.utils.gemini import VertexGeminiClient
import json
from backend.pdf_generator import generate_pdf


logger = logging.getLogger(__name__)
ExecutionEventCallback = Callable[[str, dict[str, Any]], None]


class ToolExecutionError(RuntimeError):
    pass


class AgentExecutor:
    def __init__(self, settings: Settings, mcp_server: MCPServer | None = None) -> None:
        self.settings = settings
        self.gemini = VertexGeminiClient(settings)
        self.planner = AgentPlanner(self.gemini)
        self.memory = MemoryStore(settings.memory_db_path)
        self.mcp_server = mcp_server
        self.tool_registry: dict[str, Callable[..., dict[str, Any]]] = {
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
        tool_mode: str = "direct",
        event_callback: ExecutionEventCallback | None = None,
        format_type: str = "ieee",
        page_length: str = "4-5",
        include_formulas: bool = False,
        include_diagrams: bool = False,
    ) -> dict[str, Any]:
        normalized_files = self._normalize_file_context(file_context)
        state = self._initialize_state(normalized_files)
        self._emit(event_callback, "planning", {"message": "Building execution plan"})
        self._record_step(state, "Planning")

        for trace in initial_tool_calls or []:
            if isinstance(trace, dict):
                self._apply_tool_trace(
                    tool_name=str(trace.get("tool") or "unknown"),
                    trace=trace,
                    state=state,
                )

        extracted_context = state["ocr_text"].strip()
        plan = self.planner.plan(
            user_input=user_input,
            context_text=extracted_context,
            preferred_output=preferred_output,
            upload_requested=upload_results_to_drive,
        )

        generated_content: str | None = None
        memory_info: dict[str, Any] | None = None
        output_path: Path | None = None

        for step in plan.get("workflow", []):
            if not isinstance(step, dict):
                continue
            tool_name = str(step.get("tool") or "none").strip()
            action = str(step.get("action") or f"Running {tool_name}")
            if tool_name == "none":
                self._record_step(state, action)
                continue
            if tool_name == "upload_to_drive" and not upload_results_to_drive:
                continue

            stage = self._stage_for_tool(tool_name)
            self._emit(event_callback, stage, {"message": action, "tool": tool_name})
            trace = self._execute_workflow_step(
                step=step,
                state=state,
                plan=plan,
                user_input=user_input,
                generated_content=generated_content,
                output_path=output_path,
                memory_info=memory_info,
                upload_requested=upload_results_to_drive,
                tool_mode=tool_mode,
            )
            if trace.get("status") == "error":
                logger.warning("Tool %s execution failed: %s", tool_name, trace.get("error") or trace.get("message"))
                continue

        sources = self._attach_source_reference_ids(
            self._deduplicate_sources(state["sources"])
        )

        self._emit(event_callback, "generating", {"message": "Generating final output"})
        self._record_step(state, "Generating")
        generated_content = self._generate_content(
            user_input=user_input,
            plan=plan,
            sources=sources,
            file_context=normalized_files,
            state=state,
            format_type=format_type,
            page_length=page_length,
            include_formulas=include_formulas,
            include_diagrams=include_diagrams,
        )

        content_str = generated_content if isinstance(generated_content, str) else json.dumps(generated_content, indent=2)

        memory_info = self.memory.save_run(
            topic=plan["topic"],
            input_prompt=user_input,
            output_type=plan["output_type"],
            content=content_str,
            plan=plan,
            sources=sources,
        )
        state["memory"]["memory_id"] = str(memory_info["output_id"])

        if isinstance(generated_content, dict) and plan.get("output_type") == "research_paper":
            self._emit(event_callback, "generating", {"message": f"Formatting {format_type.upper()} PDF"})
            output_path = Path(generate_pdf(generated_content, format_type=format_type))
            generated_content["pdf_path"] = str(output_path)
            generated_content["drive_link"] = None
        else:
            output_path = self._write_output_file(
                topic=plan["topic"],
                output_type=plan["output_type"],
                content=content_str,
            )

        state["memory"]["output_file"] = str(output_path)

        save_trace = self._execute_tool(
            tool_name="save_to_db",
            tool_input={
                "data": {
                    "event_type": "agent_run",
                    "topic": plan.get("topic"),
                    "input_prompt": user_input,
                    "output_type": plan.get("output_type"),
                    "memory_id": memory_info["output_id"],
                    "source_count": len(sources),
                    "output_file": str(output_path),
                }
            },
            tool_mode=tool_mode,
            run_id=memory_info["output_id"],
        )
        self._apply_tool_trace("save_to_db", save_trace, state)

        if upload_results_to_drive:
            self._emit(event_callback, "uploading", {"message": "Uploading to Google Drive"})
            upload_trace = self._execute_tool(
                tool_name="upload_to_drive",
                tool_input={"file_path": str(output_path)},
                tool_mode=tool_mode,
                run_id=memory_info["output_id"],
            )
            self._apply_tool_trace("upload_to_drive", upload_trace, state)
            if upload_trace.get("status") != "success" or not state["memory"].get("drive_link"):
                raise ToolExecutionError(
                    state.get("last_upload_error")
                    or "Google Drive upload failed before a shareable link was produced."
                )

        if state["memory"].get("drive_link"):
            self.memory.update_drive_link(
                int(memory_info["output_id"]),
                str(state["memory"]["drive_link"]),
            )

        if isinstance(generated_content, dict) and plan.get("output_type") == "research_paper":
            if state["memory"].get("drive_link"):
                generated_content["drive_link"] = state["memory"].get("drive_link")
            result = generated_content
        else:
            result = {
                "plan": plan.get("workflow", []),
                "steps": state["steps"],
                "sources": sources,
                "output": content_str,
                "drive_link": state["memory"].get("drive_link"),
                "memory_id": str(memory_info["output_id"]),
            }
        self._emit(event_callback, "completed", result)
        return result

    def execute_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_mode: str = "direct",
        run_id: int | None = None,
    ) -> dict[str, Any]:
        return self._execute_tool(tool_name, tool_input, tool_mode, run_id=run_id)

    def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_mode: str,
        run_id: int | None = None,
    ) -> dict[str, Any]:
        try:
            if tool_mode == "mcp" and self.mcp_server and self.mcp_server.started:
                output = self.mcp_server.execute(tool_name, tool_input)
                if isinstance(output, dict) and "output" in output and "tool" in output:
                    normalized_output = output.get("output")
                    normalized_status = output.get("status", "success")
                else:
                    normalized_output = output
                    normalized_status = (
                        output.get("status", "success")
                        if isinstance(output, dict)
                        else "success"
                    )
                result = {
                    "tool": tool_name,
                    "status": normalized_status,
                    "input": tool_input,
                    "output": normalized_output,
                }
            else:
                handler = self.tool_registry.get(tool_name)
                if not handler:
                    raise ToolExecutionError(f"Tool '{tool_name}' is not registered.")
                output = handler(**tool_input)
                result = {
                    "tool": tool_name,
                    "status": output.get("status", "success")
                    if isinstance(output, dict)
                    else "success",
                    "input": tool_input,
                    "output": output,
                }
        except MCPDispatchError as exc:
            result = {"tool": tool_name, "status": "error", "input": tool_input, "error": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            logger.exception("Tool execution failed: %s", tool_name)
            result = {"tool": tool_name, "status": "error", "input": tool_input, "error": str(exc)}

        if result.get("status") == "error":
            self.memory.save_event(
                event_type="tool_error",
                payload={"tool": tool_name, "error": result.get("error"), "input": tool_input},
                run_id=run_id,
            )
            return result

        self.memory.save_event(
            event_type="tool_execution",
            payload={"tool": tool_name, "input": tool_input},
            run_id=run_id,
        )
        return result

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.memory.get_history(limit=limit)

    def _tool_web_search(self, query: str, max_results: int = 5) -> dict[str, Any]:
        return web_search(query=query, max_results=max_results)

    def _tool_extract_pdf(self, file_path: str) -> dict[str, Any]:
        return extract_pdf(file_path=file_path)

    def _tool_extract_image(self, file_path: str) -> dict[str, Any]:
        return extract_image(file_path=file_path)

    def _tool_save_to_db(self, data: dict[str, Any]) -> dict[str, Any]:
        event_type = str(data.get("event_type") or "agent_event")
        payload = dict(data)
        payload.pop("event_type", None)
        return self.memory.save_event(event_type=event_type, payload=payload)

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
            "files": file_context,
            "ocr_text": extracted_text,
            "logs": [],
            "steps": [],
            "memory": {"drive_link": None},
            "last_upload_error": None,
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
        tool_mode: str = "direct",
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
        trace = self._execute_tool(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_mode=tool_mode,
            run_id=(memory_info or {}).get("output_id"),
        )
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
                if resolved.get("queries") and isinstance(resolved["queries"], list) and len(resolved["queries"]) > 0:
                    resolved["query"] = str(resolved["queries"][0])
                else:
                    fallback_query = plan.get("search_queries", [plan.get("topic", user_input)])
                    resolved["query"] = str(fallback_query[0])
            if "queries" in resolved:
                del resolved["queries"]
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
                
            # If the raw input passed parameters directly rather than nested in 'data'
            if not resolved.get("data") and any(k in resolved for k in ["event_type", "type", "topic"]):
                payload.update(resolved)
                if "type" in payload and not "event_type" in payload:
                    payload["event_type"] = payload.pop("type")
                
            payload.setdefault("event_type", "agent_run")
            payload.setdefault("topic", plan.get("topic"))
            payload.setdefault("input_prompt", user_input)
            payload.setdefault("output_type", plan.get("output_type"))
            payload.setdefault("source_count", len(state.get("sources", [])))
            payload.setdefault("has_file_context", bool(state.get("files")))
            payload.setdefault("memory_id", (memory_info or {}).get("output_id"))
            payload.setdefault("output_file", str(output_path) if output_path else None)
            payload.setdefault("drive_link", state.get("memory", {}).get("drive_link"))
            payload.setdefault("generated_preview", (generated_content or "")[:500])
            payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            return {"data": payload}

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
                current = state.get("ocr_text", "")
                state["ocr_text"] = f"{current}\n\n{extracted_text}".strip() if current else extracted_text
        elif tool_name == "upload_to_drive" and isinstance(output, dict):
            drive_link = output.get("link")
            if drive_link:
                state["memory"]["drive_link"] = str(drive_link)

    @staticmethod
    def _record_step(state: dict[str, Any], message: str) -> None:
        steps = state.setdefault("steps", [])
        if isinstance(steps, list) and (not steps or steps[-1] != message):
            steps.append(message)

    def _generate_content(
        self,
        user_input: str,
        plan: dict[str, Any],
        sources: list[dict[str, Any]],
        file_context: list[dict[str, Any]],
        state: dict[str, Any],
        format_type: str = "ieee",
        page_length: str = "4-5",
        include_formulas: bool = False,
        include_diagrams: bool = False,
    ) -> str | dict[str, Any]:
        self.gemini.ensure_available()

        source_block = "\n".join(
            [
                f"[{source['ref_id']}] {source['title']} | {source['url']}\n{source['snippet']}"
                for source in sources
            ]
        )
        file_context_block = "\n\n".join(
            [
                (
                    f"File: {item.get('file_name', 'uploaded_file')} ({item.get('file_type', 'unknown')})\n"
                    f"Extracted text:\n{(item.get('text') or '')[:3500]}"
                )
                for item in file_context
                if isinstance(item, dict)
            ]
        )

        format_instruction = self._output_format_instruction(plan.get("output_type", "summary"), format_type, page_length, include_formulas, include_diagrams)
        planning_block = "\n".join(
            [
                f"Topic: {plan.get('topic')}",
                f"Output type: {plan.get('output_type')}",
                f"Sections: {', '.join(plan.get('sections', []))}",
                f"Completed steps: {', '.join(state.get('steps', []))}",
            ]
        )

        if plan.get("output_type") == "research_paper":
            paper_prompt = (
                f"{format_instruction}\n\n"
                f"Topic/User Request: {user_input}\n\n"
                f"Research Metadata:\n{planning_block}\n\n"
                "Web Sources — synthesize these findings with inline citations [S1], [S2] etc.:\n"
                f"{source_block or 'No external sources collected. Draw on authoritative domain knowledge.'}\n\n"
                f"Uploaded File Context:\n{file_context_block or 'None.'}\n\n"
                "ADDITIONAL CONTENT REQUIREMENTS:\n"
                "1. Treat this as a systems paper about a deployable autonomous research agent, not a generic survey.\n"
                "2. Introduction: articulate the operational problem, deployment setting, and 3-4 concrete engineering contributions.\n"
                "3. Related Work: compare only relevant prior work and official platform capabilities; avoid citation padding.\n"
                "4. System Architecture: describe the input layer, UI, backend API, Gemini reasoning engine, orchestration layer, MCP integration, memory/database, and export/storage path.\n"
                "5. Agent Workflow: explain goal understanding, planning, tool routing, evidence retrieval, memory updates, and artifact export as an execution trace.\n"
                "6. Data Pipeline: include source acquisition, duplicate removal, ranking/filtering heuristics, and evidence extraction steps.\n"
                "7. Experimental Setup: use realistic evaluation dimensions such as source precision, task completion rate, latency, citation coverage, and export success rate.\n"
                "8. Results: present quantitative comparisons and ablations that look plausible for a hackathon prototype without sounding inflated.\n"
                "9. Discussion: analyze trade-offs, bottlenecks, failure modes, rate limits, and scalability constraints.\n"
                "10. Include implementation details such as model configuration, retry policy, timeout strategy, memory schema, and tool invocation flow whenever relevant.\n"
                "11. Use fewer but higher-quality references. Prefer primary papers, official documentation, and authoritative technical reports.\n"
                "12. If the provided sources are limited, keep the reference list short rather than inventing weak citations.\n"
                "13. Author = 'Autonomous Research Assistant', Affiliation = 'Autonomous Research Assistant Platform'.\n"
                "14. Do NOT include numbers in section titles (LaTeX handles it automatically).\n"
                "15. Do NOT prefix references with [1]. Write reference text directly.\n"
                "16. Return ONLY valid JSON — no markdown fences, no trailing text.\n"
                "17. CRITICAL: In references array, each entry MUST be a plain text string, NOT a dict.\n"
                "    CORRECT:   \"references\": [\"L. Zhang et al., Title, Journal, 2023.\"]\n"
                "    INCORRECT: \"references\": [{\"text\": \"L. Zhang...\"}]\n"
            )
            try:
                parsed = self.gemini.generate_json_strict(
                    prompt=paper_prompt,
                    temperature=0.2,
                    max_output_tokens=16384,
                )
                # Enforce single authoritative author — never fake placeholders
                parsed["authors"] = ["Autonomous Research Assistant"]
                parsed["affiliation"] = parsed.get("affiliation") or "Autonomous Research Assistant Platform"
                parsed["contact_email"] = parsed.get("contact_email") or "research@ara-platform.ai"

                # Normalize references: accept both string and {text: ...} formats
                raw_refs = parsed.get("references") or []
                normalized_refs: list[Any] = []
                for r in raw_refs:
                    if isinstance(r, str):
                        normalized_refs.append({"text": r})
                    elif isinstance(r, dict):
                        normalized_refs.append(r)
                parsed["references"] = normalized_refs

                return parsed
            except Exception as e:
                logger.error("Research paper generation failed: %s", e)
                return {
                    "title": user_input,
                    "authors": ["Autonomous Research Assistant"],
                    "affiliation": "Autonomous Research Assistant Platform",
                    "contact_email": "research@ara-platform.ai",
                    "abstract": (
                        f"This paper examines {user_input}. "
                        "Content generation encountered an issue; please retry."
                    ),
                    "keywords": [],
                    "sections": [],
                    "citations": [],
                    "references": [],
                }

        # Non-paper output types
        raw = self.gemini.generate_text(
            prompt=(
                f"{format_instruction}\n\nUser request: {user_input}\n\n"
                f"Agent plan:\n{planning_block}\n\n"
                f"Web sources:\n{source_block or 'No external web sources collected.'}\n\n"
                f"Uploaded file context:\n{file_context_block or 'No uploaded files.'}\n\n"
                "Requirements:\n"
                "1. Be concrete and useful.\n"
                "2. Ground factual claims in the provided sources when available.\n"
                "3. If source coverage is weak, say so briefly instead of inventing citations.\n"
                "4. End with a References section listing the cited [S#] entries."
            ),
            temperature=0.25,
            max_output_tokens=8192,
        ).strip()
        return raw

    @staticmethod
    def _output_format_instruction(output_type: str, format_type: str = "ieee", page_length: str = "4-5", include_formulas: bool = True, include_diagrams: bool = True) -> str:
        fmt = format_type.upper()
        if output_type == "research_paper":
            # Section titles must NOT include numbers — LaTeX handles numbering
            required_sections = {
                "IEEE": [
                    "Introduction",
                    "Related Work and System Context",
                    "System Architecture",
                    "Agent Workflow and Tool Orchestration",
                    "Data Acquisition and Preprocessing",
                    "Experimental Setup",
                    "Results and Analysis",
                    "Deployment, Scalability, and Limitations",
                    "Conclusion",
                ],
                "APA": [
                    "Introduction",
                    "Literature Review and Context",
                    "System Architecture",
                    "Method and Agent Workflow",
                    "Data Pipeline",
                    "Experimental Design",
                    "Results",
                    "Discussion and Operational Considerations",
                    "Conclusion",
                ],
                "ACM": [
                    "Introduction",
                    "Background and Related Work",
                    "System Architecture",
                    "Agent Workflow and Tool Orchestration",
                    "Data Processing Pipeline",
                    "Evaluation Setup",
                    "Results and Analysis",
                    "Deployment Considerations",
                    "Conclusion",
                ],
            }.get(
                fmt,
                [
                    "Introduction",
                    "System Architecture",
                    "Methodology",
                    "Experimental Setup",
                    "Results and Analysis",
                    "Conclusion",
                ],
            )

            # Format-specific reference examples — realistic, no [n] prefix
            ref_example = {
                "IEEE": 'L. Zhang, K. Ren, and H. Liu, "Adversarial Robustness in Deep Neural Networks via Input Transformation," IEEE Trans. Neural Netw. Learn. Syst., vol. 34, no. 8, pp. 4102-4115, Aug. 2023. doi: 10.1109/TNNLS.2022.3189271',
                "APA": "Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., & Polosukhin, I. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30, 5998-6008. https://doi.org/10.48550/arXiv.1706.03762",
                "ACM": "Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., Neelakantan, A., et al. 2020. Language Models are Few-Shot Learners. In Proceedings of the 34th Conference on Neural Information Processing Systems (NeurIPS '20). Curran Associates, Red Hook, NY, USA, Article 1877. https://doi.org/10.48550/arXiv.2005.14165",
            }.get(fmt, "Author, A. B. Title of article. Journal Name, vol. X, pp. 1-12, Year.")

            # Build sections JSON with 5 paragraph placeholders
            para_placeholder = ", ".join(
                [f'"<substantive paragraph {i+1}: 5-8 well-structured sentences, technical and domain-specific>"' for i in range(5)]
            )
            sections_json = "[\n" + ",\n".join(
                f'    {{"title": "{s}", "content": [{para_placeholder}]}}'
                for s in required_sections
            ) + "\n  ]"

            return (
                f"You are a domain expert writing a {fmt}-format academic paper for submission to a top-tier peer-reviewed venue.\n"
                f"The paper must be PUBLICATION-READY, equivalent to {page_length} printed pages.\n\n"
                "Produce the paper as a JSON object with EXACTLY this structure:\n"
                "{\n"
                '  "title": "A Precise, Technically Descriptive Academic Title Without Colons",\n'
                '  "authors": ["Autonomous Research Assistant"],\n'
                '  "affiliation": "Autonomous Research Assistant Platform",\n'
                '  "contact_email": "research@ara-platform.ai",\n'
                '  "abstract": "A 200-300 word structured abstract: (1) operational problem and motivation, (2) agent architecture and orchestration approach, (3) representative quantitative findings, (4) deployment implications. Single paragraph, no citations.",\n'
                '  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],\n'
                f'  "sections": {sections_json},\n'
                '  "citations": ["[S1] source title and URL used inline"],\n'
                '  "references": [\n'
                f'    {{"text": "{ref_example}"}}\n'
                "  ]\n"
                "}\n\n"
                "ABSOLUTE RULES:\n"
                "1. Section titles must NOT include numbers. Write 'Introduction' not '1. Introduction'.\n"
                "   LaTeX automatically adds section numbering — do NOT add it yourself.\n"
                "2. Reference text must NOT start with [1] or [2]. Just write the citation text directly.\n"
                "   LaTeX automatically adds \\bibitem numbering.\n"
                f"3. Include 8-12 references formatted in strict {fmt} style, unless the evidence base is smaller.\n"
                "   Use only authoritative papers, official documentation, or technical reports.\n"
                "4. EVERY section MUST have 3-5 paragraphs. Each paragraph MUST have 4-7 sentences.\n"
                f"5. Total word count should fill {page_length} two-column pages (approximately 2500-3800 words).\n"
                "6. Use formal academic English. Vary sentence length and structure. Avoid repetition and generic filler.\n"
                "7. Include specific technical details: APIs, retry logic, storage schema, evaluation metrics, and operating constraints.\n"
                "8. Write like an expert systems engineer — analytical, comparative, and implementation-focused.\n"
                "9. SMART FORMULA USAGE: Include LaTeX equations ONLY if the topic is mathematically intensive\n"
                "   (e.g. ML loss functions, optimization, signal processing, statistics). If equations are included,\n"
                "   embed them inside paragraph strings as valid LaTeX math escaped for JSON\n"
                "   (e.g. \\\\( L = -\\\\sum_{i} y_i \\\\log(\\\\hat{y}_i) \\\\)).\n"
                "   Do NOT include equations for policy, social science, or purely qualitative topics.\n"
                "10. REQUIRED TABLE USAGE: Add at least one 'table' key to a relevant section.\n"
                "    Use it for quantitative comparison, tool latency, or workflow evaluation as appropriate. Format:\n"
                '    "table": {"caption": "...", "columns": "l c c c", "header": "Method & Metric1 & Metric2 & Metric3", "rows": ["..."]}\n'
                "11. Add a 'figure_caption' key to architecture or workflow sections when the topic is system-oriented.\n"
                "12. If you mention datasets, retrieval corpora, or benchmark scenarios, describe their role and scale realistically.\n"
                "13. Do NOT output markdown, code fences, or any text outside the JSON. Return ONLY valid JSON."
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

    @staticmethod
    def _stage_for_tool(tool_name: str) -> str:
        if tool_name == "web_search":
            return "searching"
        if tool_name in {"extract_pdf", "extract_image"}:
            return "processing"
        if tool_name == "upload_to_drive":
            return "uploading"
        return "processing"

    @staticmethod
    def _emit(
        callback: ExecutionEventCallback | None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if callback is not None:
            callback(event_type, payload)
