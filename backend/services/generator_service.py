import requests
import os

def generate_section(section, topic, context):
    # 🔥 LIMIT CONTEXT (VERY IMPORTANT)
    context = context[:4000]
    api_key = os.getenv("GROQ_API_KEY")

    # 🔥 STRONG PROMPT (BETTER OUTPUT)
    prompt = f"""
You are an expert academic researcher.

Write the "{section}" section of a research paper on the topic:
"{topic}"

Use ONLY the provided research context.

---------------------
RESEARCH CONTEXT:
{context}
---------------------

INSTRUCTIONS:
- Use formal academic writing style
- Be clear, structured, and detailed
- Use proper paragraphs (no bullet points unless needed)
- Add citations like [1], [2] where appropriate
- Do NOT hallucinate facts
- Do NOT repeat sentences
- Keep it concise but informative

OUTPUT:
Return ONLY the section content (no headings like "Introduction:")
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            },
            timeout=180
        )
        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"]

        # 🔥 SAFETY CHECK
        if not result or len(result.strip()) < 50:
            return f"{section} content could not be generated properly."

        return result.strip()

    except Exception as e:
        print(f"❌ Error generating {section}:", e)
        return f"{section} generation failed."