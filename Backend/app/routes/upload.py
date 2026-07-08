from fastapi import APIRouter, UploadFile, File
from app.services.pdf_service import extract_text

router = APIRouter(prefix="/api", tags=["Upload"])


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return {"error": "Please upload a PDF"}

    pdf_bytes = await file.read()

    result = extract_text(pdf_bytes)

    return {
        "filename": file.filename,
        "pages": result["pages"],
        "characters": result["characters"],
        "preview": result["full_text"][:1500]
    }