def generate_bibtex(papers):
    entries = []

    for p in papers:
        entry = f"[{p['id']}] {p['title']}, {p['year']}. DOI: {p['doi']}"
        entries.append(entry)

    return "\n".join(entries)