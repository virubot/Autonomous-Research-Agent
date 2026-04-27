import OpenAI from "openai";
import { validateStructuredPaper } from "./paperComposer.js";

const PAPER_MODEL = process.env.GROQ_PAPER_MODEL || process.env.GROQ_MODEL || "llama-3.1-8b-instant";
const PAPER_MAX_TOKENS = Number(process.env.GROQ_PAPER_MAX_TOKENS || 8000);

const SYSTEM_PROMPT = `You are an advanced AI Research Assistant.

STRICT OUTPUT RULES (VERY IMPORTANT):

1. FORMAT CONTROL
- NEVER output raw HTML tags like <div>, <p>, <h2>, etc.
- Always return CLEAN, structured Markdown.
- Use:
  - ## for section headings
  - ### for subsections
  - Paragraphs for explanations
  - Bullet points only when needed

2. RESEARCH PAPER STRUCTURE
When in "Paper Mode", ALWAYS follow this structure:
- Title
- Abstract
- Keywords
- 1. Introduction
- 2. Methodology / Approach
- 3. Results / Analysis (if applicable)
- 4. Discussion
- 5. Conclusion
- References (if applicable)

Do NOT include unnecessary sections.

3. MATHEMATICAL FORMULAS (CRITICAL — NO GENERIC FORMULAS)
- ONLY include formulas IF the topic EXPLICITLY involves mathematical modeling, equations, or algorithms.
- Every formula MUST be UNIQUE to the specific topic being discussed.
- STRICTLY FORBIDDEN formulas (NEVER use these):
  - M = 1/T Σ S(E(Xi), Yi) or any variant
  - Any generic "evaluation metric" or "accuracy" placeholder formula
  - Any formula reused from a previous paper or generic template
- If you include a formula:
  - It must be derived from or directly relevant to the specific topic
  - It must be explained in context below it
  - Write formulas in plain readable format. DO NOT use LaTeX format (\\[ \\], $$ $$).
- If no math is needed for this topic -> DO NOT include any formula at all.
- When in doubt -> DO NOT include a formula.

4. DIAGRAMS / FLOWCHARTS (CRITICAL — NO GENERIC DIAGRAMS)
- ONLY generate architecture/workflow descriptions IF the topic involves system design, architecture, or a real process pipeline.
- STRICTLY FORBIDDEN diagrams:
  - "Problem → Data → Feature → Decision" or any variant
  - "Problem Definition → Data Acquisition → Feature Analysis → Decision Engine → Evaluation Output"
  - Any generic 4-5 step pipeline that could apply to any topic
- If you include a diagram/flow:
  - Every step must be SPECIFIC to the topic (use actual component names, actual process steps)
  - It must describe the real workflow of the specific system being discussed
- If the topic is theoretical, philosophical, or descriptive -> DO NOT include any diagram.
- When in doubt -> DO NOT include a diagram.

5. CONTENT QUALITY — UNIQUENESS IS MANDATORY
- Every response MUST be unique to the specific topic
- Do NOT reuse content structures, paragraphs, or phrasings across different topics
- Avoid generic or repetitive statements
- Avoid filler content
- Ensure academic, professional tone
- Keep explanations precise and meaningful

6. JSON / API SAFETY (IMPORTANT FOR YOUR BACKEND)
- Output MUST be clean text (NO broken JSON)
- Avoid special characters that break parsing
- Do NOT include stray backticks or malformed structures

7. ERROR PREVENTION
- Do NOT hallucinate structure (like fake HTML blocks)
- No Mermaid syntax, No LaTeX syntax, No raw diagram code
- If unsure -> skip formula/diagram instead of generating wrong ones

8. RESPONSE MODE BEHAVIOR

If Chat Mode:
-> Give concise, clean, readable answer

If Paper Mode:
-> Generate full structured research paper (as defined above)

9. FINAL VALIDATION CHECKLIST (MANDATORY BEFORE OUTPUT)
Before generating output, internally verify:
✔ No HTML tags
✔ No generic formulas (especially M = 1/T Σ ...)
✔ No generic pipeline diagrams (especially Problem → Data → Feature → Decision)
✔ Formula included ONLY if topic demands math
✔ Diagram included ONLY if topic involves system/architecture
✔ All content is unique and topic-specific
✔ Proper structure
✔ Clean formatting

If any violation -> fix before output`;

function getClient() {
  const apiKey = process.env.GROQ_API_KEY || process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("Missing GROQ_API_KEY for paper generation.");
  }

  return new OpenAI({
    apiKey,
    baseURL: "https://api.groq.com/openai/v1"
  });
}

function extractJsonPayload(content) {
  try {
    let cleaned = String(content ?? "")
      .replace(/```json\s*/gi, "")
      .replace(/```/g, "")
      .trim();

    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");

    if (start === -1 || end === -1) return null;

    let jsonString = cleaned.slice(start, end + 1);

    // Fix common JSON issues
    jsonString = jsonString.replace(/,\s*}/g, "}");
    jsonString = jsonString.replace(/,\s*]/g, "]");
    jsonString = jsonString.replace(/[“”]/g, '"');

    return JSON.parse(jsonString);

  } catch (err) {
    console.error("Bad JSON:", content);
    return null; // ✅ prevent crash
  }
}

export async function chatResponse(prompt) {
  try {
    if (prompt.length > 500) throw new Error("Input too long");
    const client = getClient();

    const res = await client.chat.completions.create({
      model: "llama-3.1-8b-instant",
      max_tokens: 4000,
      messages: [
        {
          role: "system",
          content: SYSTEM_PROMPT + "\n\nMODE: Chat Mode. Give a concise, clean, readable answer."
        },
        {
          role: "user",
          content: prompt
        }
      ]
    });

    return res.choices[0].message.content;

  } catch (err) {
    console.error("Chat Error:", err.message);
    return "⚠️ Error generating response.";
  }
}

/**
 * Builds a section-specific prompt that requests topic-relevant content.
 * Architecture section: requests a topic-specific workflow/flow array.
 * Results section: requests a topic-specific LaTeX equation ONLY if the topic involves math.
 * All sections: enforce uniqueness, no generic content.
 */
function buildSectionPrompt(section, topic) {
  const baseRules = `
Topic: ${topic}

STRICT RULES:
- Return ONLY valid JSON
- Use double quotes for ALL keys and strings
- No trailing commas
- No missing colons
- No text outside JSON

CONTENT RULES:
- Write VERY DETAILED content specific to "${topic}"
- Each paragraph must be 120–150 words
- Generate 4–6 paragraphs
- Use formal IEEE tone
- Every sentence must be UNIQUE to this specific topic
- DO NOT use generic filler content`;

  if (section === "abstract") {
    return `Generate ONLY the abstract section.
${baseRules}

FORMAT:
{
  "abstract": "200-250 words paragraph specifically about ${topic}"
}`;
  }

  if (section === "architecture") {
    return `Generate ONLY the architecture section.
${baseRules}

ADDITIONAL REQUIREMENT — TOPIC-SPECIFIC ARCHITECTURE FLOW:
- Also generate a "architectureFlow" array: 4-6 steps describing the ACTUAL system/process architecture for "${topic}"
- Each step must use REAL component names or process steps specific to this topic
- FORBIDDEN: generic steps like "Problem Definition", "Data Acquisition", "Feature Analysis", "Decision Engine", "Evaluation Output"
- If "${topic}" does not involve system design or architecture, set architectureFlow to an empty array []

FORMAT:
{
  "architecture": ["paragraph1", "paragraph2", "paragraph3", "paragraph4"],
  "architectureFlow": ["TopicSpecificStep1", "TopicSpecificStep2", "TopicSpecificStep3", "TopicSpecificStep4"]
}`;
  }

  if (section === "results") {
    return `Generate ONLY the results section.
${baseRules}

ADDITIONAL REQUIREMENT — TOPIC-SPECIFIC EQUATION:
- If "${topic}" involves mathematical modeling, algorithms, or quantitative analysis:
  - Include an "equation" object with "plainText" (plain readable format) and "caption" (explanation)
  - The equation MUST be derived from or directly relevant to "${topic}"
  - FORBIDDEN: M = 1/T Σ S(E(Xi), Yi) or any generic evaluation metric formula
- If "${topic}" does NOT require math, set "equation" to null

FORMAT:
{
  "results": ["paragraph1", "paragraph2", "paragraph3", "paragraph4"],
  "equation": {
    "plainText": "topic-specific plain text formula here",
    "caption": "Explanation of what this equation represents in context of ${topic}"
  }
}

OR if no math is needed:
{
  "results": ["paragraph1", "paragraph2", "paragraph3", "paragraph4"],
  "equation": null
}`;
  }

  // Default for introduction, methodology, conclusion, references
  return `Generate ONLY the ${section} section.
${baseRules}

FORMAT:
{
  "${section}": ${section === "references"
    ? '["reference1", "reference2", "reference3", "reference4", "reference5", "reference6"]'
    : '["paragraph1", "paragraph2", "paragraph3", "paragraph4"]'
  }
}`;
}

export async function generatePaper(topic) {
  try {
    const client = getClient();

    const sections = [
      "abstract",
      "introduction",
      "methodology",
      "architecture",
      "results",
      "conclusion",
      "references"
    ];

    const paper = {
      title: topic,
      abstract: "",
      keywords: [],
      architectureFlow: [],
      introduction: [],
      methodology: [],
      architecture: [],
      results: [],
      conclusion: [],
      references: [],
      equation: null
    };

    for (const section of sections) {
      let data = null;

      for (let retry = 0; retry < 3; retry++) {
        try {
          const res = await client.chat.completions.create({
            model: PAPER_MODEL,
            temperature: 0.3,
            max_tokens: 1200,
            messages: [
              {
                role: "system",
                content: SYSTEM_PROMPT + "\n\nMODE: Paper Mode. You are an IEEE research paper writer."
              },
              {
                role: "user",
                content: buildSectionPrompt(section, topic)
              }
            ]
          });

          data = extractJsonPayload(res.choices[0].message.content);

          if (data) break; // ✅ success

        } catch (err) {
          console.error("Retry error:", err.message);
        }
      }

      if (!data) {
        console.warn(`Skipping ${section} due to JSON errors`);
        continue; // ✅ don't crash
      }

      if (section === "abstract") {
        paper.abstract = data.abstract || "";
      } else if (section === "architecture") {
        paper.architecture = data?.architecture || [];
        // Extract topic-specific architecture flow from LLM response
        if (Array.isArray(data?.architectureFlow) && data.architectureFlow.length >= 3) {
          paper.architectureFlow = data.architectureFlow;
        }
      } else if (section === "results") {
        paper.results = data?.results || [];
        // Extract topic-specific equation from LLM response
        if (data?.equation && data.equation.plainText && data.equation.caption) {
          paper.equation = data.equation;
        }
      } else {
        paper[section] = data?.[section] || [];
      }
    }

    return paper;

  } catch (err) {
    console.error("Paper Error:", err.message);
    throw err;
  }
}