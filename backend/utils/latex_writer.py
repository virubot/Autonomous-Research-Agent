from pylatex import Document, Section, Command
from pylatex.utils import NoEscape

def clean_text(text):
    if not text:
        return ""

    replacements = {
        "≥": r"$\geq$",
        "≤": r"$\leq$",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "#": r"\#",
        "$": r"\$"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


def create_pdf(content):
    doc = Document(documentclass="IEEEtran")

    doc.preamble.append(Command("title", "AI Generated Research Paper"))
    doc.preamble.append(Command("author", "Your Name"))
    doc.append(NoEscape(r"\maketitle"))

    for section, text in content.items():
        if section != "References":
            with doc.create(Section(section)):
                doc.append(clean_text(text))

    doc.append(NoEscape(r"\section*{References}"))
    doc.append(clean_text(content.get("References", "No references")))

    try:
        doc.generate_pdf("research_paper", clean_tex=False)
        print("✅ PDF generated successfully")

    except Exception as e:
        print("❌ PDF generation failed:", e)