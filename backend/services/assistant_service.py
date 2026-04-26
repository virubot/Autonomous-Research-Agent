from backend.services.semantic_service import fetch_papers
from backend.services.arxiv_service import search_arxiv
from backend.services.rag_service import RAG
from backend.utils.pdf_reader import download_pdf, extract_text_from_pdf
from backend.services.llm_service import ask_llm


def intelligent_assistant(query: str):

    print("🔍 Query:", query)

    # ----------------------------
    # STEP 1: FETCH PAPERS
    # ----------------------------
    semantic_papers = fetch_papers(query)
    arxiv_papers = search_arxiv(query)

    papers = semantic_papers + arxiv_papers

    print(f"📄 Papers fetched: {len(papers)}")

    if not papers:
        return {"answer": "No research papers found."}

    # ----------------------------
    # STEP 2: EXTRACT TEXT
    # ----------------------------
    chunks = []

    for i, p in enumerate(papers[:5]):
        text = ""

        if p.get("pdf"):
            try:
                file_path = download_pdf(p["pdf"], f"paper_{i}.pdf")
                if file_path:
                    text = extract_text_from_pdf(file_path)[:3000]
            except Exception as e:
                print("PDF ERROR:", e)

        if not text and p.get("abstract"):
            text = p["abstract"]

        if not text:
            text = p.get("title", "")

        sentences = text.split(".")
        for j in range(0, len(sentences), 3):
            chunk = ". ".join(sentences[j:j+3])
            if chunk.strip():
                chunks.append(chunk)

    print(f"🧩 Chunks created: {len(chunks)}")

    if not chunks:
        return {"answer": "No usable content found."}

    # ----------------------------
    # STEP 3: RAG
    # ----------------------------
    rag = RAG()
    rag.add_documents(chunks)

    relevant_chunks = rag.query(query, k=5)

    context = "\n".join(relevant_chunks)[:4000]

    print("📚 Context length:", len(context))

    # ----------------------------
    # STEP 4: LLM
    # ----------------------------
    prompt = f"""
You are an AI research assistant.

Use the following research context to answer clearly and professionally.

Context:
{context}

Question:
{query}

Give:
- clear explanation
- key insights
- research gaps (if any)
"""

    try:
        answer = ask_llm(prompt)

        print("🧠 LLM RAW ANSWER:", answer)

        # 🔥 SAFETY CHECK
        if not answer or len(answer.strip()) < 5:
            print("⚠️ Empty LLM response, using fallback")
            answer = f"Based on research:\n\n{context[:1000]}"

    except Exception as e:
        print("❌ LLM FAILED:", e)
        answer = f"Error generating answer: {str(e)}"

    # ----------------------------
    # RETURN
    # ----------------------------
    return {
        "answer": answer,
        "sources": papers[:5]
    }