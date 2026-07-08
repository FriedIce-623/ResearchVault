from fastapi import APIRouter, HTTPException
from app.database import papers
from app.models.paper import CompareRequest
from app.services.claude_service import compare_papers

router = APIRouter()


@router.post("")
async def compare(req: CompareRequest):
    if req.compare_all:
        paper_docs = []
        async for p in papers.find({}).limit(20):
            p.pop("_id", None)
            paper_docs.append(p)
        if len(paper_docs) < 2:
            raise HTTPException(400, "Need at least 2 papers in your library to compare")
    else:
        if not req.paper_ids or len(req.paper_ids) < 2:
            raise HTTPException(400, "Need at least 2 paper_ids, or set compare_all: true")
        paper_docs = []
        async for p in papers.find({"paper_id": {"$in": req.paper_ids}}):
            p.pop("_id", None)
            paper_docs.append(p)
        if not paper_docs:
            raise HTTPException(404, "No papers found with those IDs")

    return compare_papers(paper_docs, req.dimensions)