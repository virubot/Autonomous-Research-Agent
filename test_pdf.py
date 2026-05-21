import asyncio
from backend.utils.config import get_settings
from backend.agent.executor import AgentExecutor

async def main():
    settings = get_settings()
    executor = AgentExecutor(settings)
    
    print("Generating paper...")
    result = await asyncio.to_thread(
        executor.run,
        "Vertex AI Multimodal Capabilities",
        "research_paper",
        None,
        False,
        None,
        "direct",
        None,
        "ieee"
    )
    print("Keys in result:", result.keys())
    if 'pdf_path' in result:
        print("PDF PATH:", result['pdf_path'])
            
if __name__ == "__main__":
    asyncio.run(main())
