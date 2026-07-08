import re
import fitz

def extract_text(pdf_bytes: bytes) -> dict:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text = []
    for page in doc:
        full_text.append(page.get_text("text"))  # force string mode

    num_pages = len(doc)
    doc.close()

    full_text = "".join(full_text)

    return {
        "pages": num_pages,
        "characters": len(full_text),
        "full_text": full_text,
        "sections": split_sections(full_text)
    }


def split_sections(text: str) -> dict:
    section_titles = [
        "abstract",
        "introduction",
        "related work",
        "background",
        "method",
        "methods",
        "methodology",
        "experimental setup",
        "experiments",
        "results",
        "discussion",
        "conclusion",
        "references"
    ]

    lower = text.lower()
    positions = []

    for title in section_titles:
        match = re.search(rf"\b{re.escape(title)}\b", lower)
        if match:
            positions.append((match.start(), title))

    positions.sort()

    sections = {}

    for i, (start, title) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        sections[title] = text[start:end].strip()

    return {
        "abstract": sections.get("abstract", ""),
        "introduction": sections.get("introduction", ""),
        "methodology": (
            sections.get("methodology")
            or sections.get("methods")
            or sections.get("method")
            or ""
        ),
        "results": (
            sections.get("results")
            or sections.get("experiments")
            or ""
        ),
        "conclusion": sections.get("conclusion", "")
    }