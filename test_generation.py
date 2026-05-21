import asyncio
from backend.utils.config import get_settings
from backend.agent.executor import AgentExecutor
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    settings = get_settings()
    executor = AgentExecutor(settings)
    
    print("\nTesting APA...")
    try:
        res = executor.run(
            user_input="Psychological effects of AI companions",
            preferred_output="research_paper",
            format_type="apa",
            page_length="4-5",
            include_formulas=False,
            include_diagrams=True
        )
        print("APA Success:", res.get("pdf_path"))
    except Exception as e:
        print("APA Failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
