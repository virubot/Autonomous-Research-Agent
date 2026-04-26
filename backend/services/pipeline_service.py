from backend.services.semantic_service import fetch_papers
from backend.utils.bibtex_parser import generate_bibtex
from backend.utils.plagiarism import check_plagiarism
from backend.utils.latex_writer import create_pdf
from backend.core.agents import research_agent, analysis_agent, writer_agent
from backend.services.rag_service import RAG
from backend.utils.pdf_reader import download_pdf, extract_text_from_pdf


def run_pipeline(topic: str):

    papers = fetch_papers(topic)

    if not papers:
        papers = [{
            "id": 1,
            "title": f"Study on {topic}",
            "abstract": f"This paper discusses {topic}.",
            "year": 2024,
            "doi": "N/A",
            "pdf": None
        }]

    chunks = []

    for i, p in enumerate(papers):
        text = ""

        if p.get("pdf"):
            try:
                file_path = download_pdf(p["pdf"], f"paper_{i}.pdf")
                if file_path:
                    text = extract_text_from_pdf(file_path)[:5000]
            except:
                pass

        if not text and p.get("abstract"):
            text = p["abstract"]

        if not text:
            text = p.get("title", "")

        sentences = text.split(".")
        for j in range(0, len(sentences), 3):
            chunk = ". ".join(sentences[j:j+3])
            if chunk.strip():
                chunks.append(chunk)

    if not chunks:
        return {"error": "No data found"}

    chunks = chunks[:100]

    rag = RAG()
    rag.add_documents(chunks)

    relevant_chunks = rag.query(topic, k=5)
    rag_context = "\n".join(relevant_chunks)[:4000]

    research_summary = research_agent(topic, rag_context)
    analysis = analysis_agent(topic, research_summary)
    content = writer_agent(topic, rag_context)

    if not isinstance(content, dict):
        content = {"Introduction": "Failed", "Conclusion": "Failed"}

    similarity = check_plagiarism(content.get("Introduction", ""), [rag_context])

    try:
        content["References"] = generate_bibtex(papers)
    except:
        content["References"] = "No references"

    try:
        create_pdf(content)
    except:
        pass

    return {
        "summary": research_summary,
        "analysis": analysis,
        "content": content,
        "plagiarism": similarity
    }