import fitz  # PyMuPDF
import requests
import os

def download_pdf(url, filename="paper.pdf"):
    try:
        response = requests.get(url, timeout=10)
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename
    except:
        return None

def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)

    for page in doc:
        text += page.get_text()

    return text