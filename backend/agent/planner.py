from __future__ import annotations

from typing import Any

from backend.utils.gemini import VertexGeminiClient


SUPPORTED_OUTPUT_TYPES = {
    "research_paper",
    "summary",
    "speech",
    "notes",
    "project_plan",
}


class AgentPlanner:
    def __init__(self, gemini: VertexGeminiClient) -> None:
        self.gemini = gemini

    def plan(
        self,
        user_input: str,
        context_text: str = "",
        preferred_output: str | None = None,
        upload_requested: bool = False,
    ) -> dict[str, Any]:
        raw = self._plan_with_gemini(
            user_input=user_input,
            context_text=context_text,
            preferred_output=preferred_output,
            upload_requested=upload_requested,
        )
        return self._normalize_plan(raw, user_input, preferred_output, upload_requested)

    def _plan_with_gemini(
        self,
        user_input: str,
        context_text: str,
        preferred_output: str | None,
        upload_requested: bool,
    ) -> dict[str, Any]:
        context_preview = context_text[:2500] if context_text else ""
        prompt = f"""
You are an autonomous research planning agent.
Create a concise execution plan for the request and respond in JSON.

Allowed output_type values:
- research_paper
- summary
- speech
- notes
- project_plan

Allowed tool names:
- web_search
- extract_pdf
- extract_image
- save_to_db
- upload_to_drive
- none

Workflow rules:
- Use `web_search` for fresh external grounding when the user asks for current or factual research context.
- Use `none` for reasoning or writing steps that do not call a tool.
- Use `save_to_db` after content generation.
- Use `upload_to_drive` only when upload_requested is true.
- Keep the workflow short and executable.

JSON schema:
{{
  "topic": "string",
  "output_type": "one allowed value",
  "sections": ["section 1", "section 2"],
  "search_queries": ["query 1", "query 2"],
  "workflow": [
    {{
      "step": 1,
      "action": "short action description",
      "tool": "tool name",
      "input": {{}}
    }}
  ]
}}

User input:
{user_input}

Preferred output type (optional):
{preferred_output or "not provided"}

Upload requested:
{"yes" if upload_requested else "no"}

File context (optional):
{context_preview or "none"}
"""
        return self.gemini.generate_json(prompt)

    def _normalize_plan(
        self,
        raw: dict[str, Any],
        user_input: str,
        preferred_output: str | None,
        upload_requested: bool,
    ) -> dict[str, Any]:
        topic = str(raw.get("topic") or user_input).strip()
        output_type = self._normalize_output_type(
            str(raw.get("output_type") or ""), user_input, preferred_output
        )

        sections = raw.get("sections")
        if not isinstance(sections, list) or not sections:
            sections = self._default_sections(output_type)

        search_queries = raw.get("search_queries")
        if not isinstance(search_queries, list):
            search_queries = [topic]

        cleaned_queries = [str(q).strip() for q in search_queries if str(q).strip()]
        if not cleaned_queries:
            cleaned_queries = [topic]
        cleaned_queries = cleaned_queries[:3]

        workflow = raw.get("workflow")
        if not isinstance(workflow, list) or not workflow:
            workflow = self._default_workflow(cleaned_queries[0], upload_requested)

        normalized_workflow: list[dict[str, Any]] = []
        for index, item in enumerate(workflow, start=1):
            if not isinstance(item, dict):
                continue
            tool = str(item.get("tool") or "none").strip()
            if tool not in {
                "web_search",
                "extract_pdf",
                "extract_image",
                "save_to_db",
                "upload_to_drive",
                "none",
            }:
                tool = "none"

            raw_input = item.get("input", {})
            if not isinstance(raw_input, dict):
                raw_input = {"query": str(raw_input)}

            normalized_workflow.append(
                {
                    "step": int(item.get("step") or index),
                    "action": str(item.get("action") or "Execute planned step"),
                    "tool": tool,
                    "input": raw_input,
                }
            )

        if upload_requested and not any(
            step.get("tool") == "upload_to_drive" for step in normalized_workflow
        ):
            normalized_workflow.append(
                {
                    "step": len(normalized_workflow) + 1,
                    "action": "Upload the generated artifact to Google Drive",
                    "tool": "upload_to_drive",
                    "input": {},
                }
            )

        if not any(step.get("tool") == "save_to_db" for step in normalized_workflow):
            normalized_workflow.append(
                {
                    "step": len(normalized_workflow) + 1,
                    "action": "Persist the run metadata",
                    "tool": "save_to_db",
                    "input": {},
                }
            )

        if not normalized_workflow:
            normalized_workflow = self._default_workflow(cleaned_queries[0], upload_requested)

        return {
            "topic": topic,
            "output_type": output_type,
            "sections": sections,
            "search_queries": cleaned_queries,
            "workflow": normalized_workflow,
        }

    @staticmethod
    def _default_workflow(query: str, upload_requested: bool) -> list[dict[str, Any]]:
        workflow = [
            {
                "step": 1,
                "action": "Search fresh web sources for grounding context",
                "tool": "web_search",
                "input": {"query": query, "max_results": 5},
            },
            {
                "step": 2,
                "action": "Synthesize the final response from collected context",
                "tool": "none",
                "input": {},
            },
            {
                "step": 3,
                "action": "Persist the run metadata",
                "tool": "save_to_db",
                "input": {},
            },
        ]
        if upload_requested:
            workflow.append(
                {
                    "step": 4,
                    "action": "Upload the generated artifact to Google Drive",
                    "tool": "upload_to_drive",
                    "input": {},
                }
            )
        return workflow

    def _normalize_output_type(
        self,
        candidate: str,
        user_input: str,
        preferred_output: str | None,
    ) -> str:
        if preferred_output and preferred_output in SUPPORTED_OUTPUT_TYPES:
            return preferred_output
        if candidate in SUPPORTED_OUTPUT_TYPES:
            return candidate
        return self._detect_output_type(user_input)

    @staticmethod
    def _detect_output_type(user_input: str) -> str:
        lowered = user_input.lower()
        if "speech" in lowered or "talk" in lowered or "presentation" in lowered:
            return "speech"
        if "project plan" in lowered or "roadmap" in lowered or "milestone" in lowered:
            return "project_plan"
        if "note" in lowered or "bullet" in lowered:
            return "notes"
        if "summary" in lowered or "summarize" in lowered:
            return "summary"
        return "research_paper"

    @staticmethod
    def _default_sections(output_type: str) -> list[str]:
        if output_type == "research_paper":
            return [
                "Abstract",
                "Introduction",
                "Approach",
                "Findings",
                "Conclusion",
            ]
        if output_type == "summary":
            return ["Overview", "Key Findings", "Conclusion"]
        if output_type == "speech":
            return ["Opening", "Key Points", "Call to Action"]
        if output_type == "notes":
            return ["Main Notes", "Important Facts", "Action Items"]
        return ["Goal", "Scope", "Milestones", "Risks", "Next Steps"]
