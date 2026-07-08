from typing import Any
from app.database import papers

_TEXT_SECTIONS = [
    "key_insights",
    "limitations",
    "architecture",
    "training_strategy",
    "preprocessing",
    "proofs_or_derivations",
    "applicability",
]


async def retrieve(question: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Return top_k chunks from stored papers ranked by keyword overlap with question.
    Each chunk: {"paper_id": str, "section": str, "text": str}
    """
    try:
        docs = await papers.find({}).to_list(length=200)
    except Exception:
        return []

    chunks: list[dict[str, Any]] = []
    for doc in docs:
        paper_id = str(doc.get("paper_id") or doc["_id"])
        for section in _TEXT_SECTIONS:
            text = doc.get(section)
            if isinstance(text, str) and text.strip():
                chunks.append({"paper_id": paper_id, "section": section, "text": text})

    if not chunks:
        return []

    question_terms = set(question.lower().split())

    def _score(chunk: dict) -> int:
        return sum(1 for w in chunk["text"].lower().split() if w in question_terms)

    chunks.sort(key=_score, reverse=True)
    return chunks[:top_k]
