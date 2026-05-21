import requests
import os

def ask_llm(prompt: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "GROQ_API_KEY not found in environment"
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI research assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            },
            timeout=180
        )

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("LLM ERROR:", e)
        return f"LLM Error: {str(e)}"