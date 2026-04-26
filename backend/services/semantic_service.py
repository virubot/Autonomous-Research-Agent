import requests
from bs4 import BeautifulSoup

def fetch_papers(query):
    url = f"https://arxiv.org/search/?query={query}&searchtype=all"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    papers = []

    results = soup.find_all("li", class_="arxiv-result")

    for i, r in enumerate(results[:5], 1):
        title = r.find("p", class_="title").text.strip()
        abstract = r.find("span", class_="abstract-full").text.strip()

        papers.append({
            "id": i,
            "title": title,
            "abstract": abstract,
            "year": None,
            "doi": "N/A",
            "pdf": None
        })

    print("📊 Papers fetched:", len(papers))
    return papers