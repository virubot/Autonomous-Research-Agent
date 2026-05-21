from backend.pdf_generator import generate_pdf

test_data = {
    "title": "A Study of Artificial Intelligence",
    "abstract": "This is an abstract about AI and how it works.",
    "keywords": ["AI", "Machine Learning", "Neural Networks"],
    "sections": [
        {"title": "1. Introduction", "content": ["AI has evolved significantly."]},
        {"title": "2. Methodology", "content": ["We used a large language model."]}
    ],
    "citations": ["Citation A"],
    "references": [{"text": "Smith, J. (2025). AI Research."}]
}

try:
    path = generate_pdf(test_data, "apa", "generated_outputs")
    print(f"Success! {path}")
except Exception as e:
    print(f"Error: {e}")
