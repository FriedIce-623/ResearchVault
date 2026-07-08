import uuid

from fastapi import APIRouter, UploadFile, File, Form

from app.database import papers, datasets
from app.services.pdf_service import extract_text
from app.services.claude_service import detect_paper_type, extract_paper

router = APIRouter(prefix="/api/ingest", tags=["Ingest"])


@router.post("/upload")
async def ingest_upload(file: UploadFile = File(...), link: str | None = Form(None)):
    if file.content_type != "application/pdf":
        return {"error": "Please upload a PDF"}

    pdf_bytes = await file.read()
    text = extract_text(pdf_bytes)["full_text"]

    paper_type = detect_paper_type(text)
    data = extract_paper(text, paper_type)

    if link and not data.get("link"):
        data["link"] = link

    paper_id = str(uuid.uuid4())
    dataset_entries = data.pop("datasets", [])

    dataset_names = []
    for ds in dataset_entries:
        name = ds.get("dataset_name")
        if not name:
            continue
        dataset_names.append(name)
        existing = await datasets.find_one({"dataset_name": name})
        if existing:
            await datasets.update_one(
                {"_id": existing["_id"]}, {"$addToSet": {"paper_ids": paper_id}}
            )
        else:
            await datasets.insert_one({**ds, "paper_ids": [paper_id]})

    await papers.insert_one({
        "paper_id": paper_id,
        "paper_type": paper_type,
        "datasets": dataset_names,
        **data,
    })

    return {"paper_id": paper_id, "paper_type": paper_type, "data": data}
