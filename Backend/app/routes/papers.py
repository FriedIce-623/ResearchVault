from fastapi import APIRouter, HTTPException
from app.database import papers, datasets

router = APIRouter(prefix="/api/papers", tags=["Papers"])

_LIST_PROJECTION = {
    "_id": 0,
    "paper_id": 1,
    "paper_type": 1,
    "name": 1,
    "authors": 1,
    "key_insights": 1,
    "architecture": 1,
    "date_of_publication": 1,
}


@router.get("")
async def list_papers(paper_type: str | None = None):
    query = {"paper_type": paper_type} if paper_type else {}
    cursor = papers.find(query, _LIST_PROJECTION).sort("date_of_publication", -1)
    return await cursor.to_list(length=200)


@router.get("/search")
async def search_papers(q: str, paper_type: str | None = None):
    query: dict = {"$text": {"$search": q}}
    if paper_type:
        query["paper_type"] = paper_type

    projection = {**_LIST_PROJECTION, "score": {"$meta": "textScore"}}
    cursor = papers.find(query, projection).sort([("score", {"$meta": "textScore"})]).limit(50)
    docs = await cursor.to_list(length=50)
    for d in docs:
        d["relevance_score"] = d.pop("score", 0)
    return docs


@router.get("/datasets/all")
async def list_all_datasets():
    cursor = datasets.find({}, {"_id": 0})
    return await cursor.to_list(length=500)


@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    doc = await papers.find_one({"paper_id": paper_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Paper not found")
    return doc


@router.delete("/{paper_id}")
async def delete_paper(paper_id: str):
    result = await papers.delete_one({"paper_id": paper_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Paper not found")
    await datasets.update_many(
        {"paper_ids": paper_id}, {"$pull": {"paper_ids": paper_id}}
    )
    return {"deleted": paper_id}
