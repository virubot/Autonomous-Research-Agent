from arxiv import Client, SortCriterion
import arxiv

arxiv_client = Client()

def search_arxiv(query: str):

    search = arxiv.Search(
        query=query,
        max_results=5,
        sort_by=SortCriterion.Relevance
    )

    results = arxiv_client.results(search)

    papers = []

    for paper in results:
        papers.append({
            "id": paper.entry_id,
            "title": paper.title,
            "abstract": paper.summary,
            "pdf": paper.pdf_url,
            "link": paper.entry_id,
            "year": paper.updated.year
        })

    return papers