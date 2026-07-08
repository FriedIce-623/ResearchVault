from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import IndexModel

from app.database import db, papers, datasets
from app.routes.ask import router as ask_router
from app.routes.upload import router as upload_router
from app.routes.compare import router as compare_router
from app.routes.papers import router as papers_router
from app.routes.ingest import router as ingest_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.papers.create_indexes([
        IndexModel("paper_id", unique=True),
        IndexModel("name"),
        IndexModel("paper_type"),
        IndexModel("date_of_publication"),
        IndexModel("authors"),
        IndexModel("datasets"),
        IndexModel("architecture"),
        IndexModel("key_techniques"),
        IndexModel("preprocessing"),
        IndexModel("training_strategy"),
        IndexModel([
            ("name", "text"),
            ("key_insights", "text"),
            ("authors", "text"),
            ("architecture", "text"),
            ("limitations", "text")
        ])
    ])

    await db.datasets.create_indexes([
        IndexModel("dataset_name"),
        IndexModel("paper_ids"),
        IndexModel("public"),
        IndexModel("samples"),
        IndexModel("support"),
        IndexModel("classes"),
        IndexModel("task"),
        IndexModel("modality"),
        IndexModel([
            ("dataset_name", "text"),
            ("key_insights", "text"),
            ("task", "text"),
            ("modality", "text")
        ])
    ])

    yield


app = FastAPI(
    title="ResearchVault API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(compare_router, prefix="/api/compare", tags=["compare"])
app.include_router(papers_router)
app.include_router(ingest_router)


@app.get("/")
async def root():
    return {"message": "ResearchVault backend is running!"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "papers": await papers.count_documents({}),
        "datasets": await datasets.count_documents({})
    }