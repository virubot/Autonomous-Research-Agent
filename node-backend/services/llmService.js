import OpenAI from "openai";
import { validateStructuredPaper } from "./paperComposer.js";

const PAPER_MODEL = process.env.GROQ_PAPER_MODEL || process.env.GROQ_MODEL || "llama-3.1-8b-instant";
const PAPER_MAX_TOKENS = Number(process.env.GROQ_PAPER_MAX_TOKENS || 8000);

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
    jsonString = jsonString.replace(/(\w+)\s*:/g, '"$1":');
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
      max_tokens: 6000,
      messages: [
        {
          role: "system",
          content: "You are a concise AI assistant."
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
      references: []
    };

    for (const section of sections) {
      let data = null;

      for (let retry = 0; retry < 3; retry++) {
        try {
          const res = await client.chat.completions.create({
            model: PAPER_MODEL,
            temperature: 0.7,
            max_tokens: 1200,
            messages: [
              {
                role: "system",
                content: "You are an IEEE research paper writer. Return ONLY valid JSON."
              },
              {
                role: "user",
                content: `
Generate ONLY the ${section} section.

Topic: ${topic}

STRICT RULES:
- Return ONLY valid JSON
- Use double quotes for ALL keys and strings
- No trailing commas
- No missing colons
- No text outside JSON

CONTENT RULES:
- Write VERY DETAILED content
- Each paragraph must be 120–150 words
- Generate 4–6 paragraphs
- Use formal IEEE tone

FORMAT:
{
  "${section}": ${section === "abstract"
                    ? '"200-250 words paragraph"'
                    : '["long paragraph", "long paragraph", "long paragraph"]'
                  }
}
`
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