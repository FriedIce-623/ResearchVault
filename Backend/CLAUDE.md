# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ResearchVault is an AI-powered academic paper management backend. Users upload PDFs; the system extracts text, classifies the paper type (empirical/survey/theoretical) via Claude, extracts structured metadata using type-specific tool calls, and stores everything in MongoDB. A Q&A feature lets users ask questions over their paper library using RAG-style retrieved chunks.

## Development Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management (Python 3.12).

```bash
# Install dependencies
uv sync

# Run the development server
uv run uvicorn app.main:app --reload

# Run with a specific port
uv run uvicorn app.main:app --reload --port 8001
```

## Environment Variables

Requires a `.env` file with:

- `MONGODB_URI` — MongoDB connection string
- `DATABASE_NAME` — defaults to `researchvault` if not set
- `ANTHROPIC_API_KEY` — for all Claude API calls

## Architecture

### Request flow for PDF upload

Two upload routes exist:

- `POST /api/upload` — `pdf_service.extract_text()` only; returns raw text + a preview. Does not touch the database. Used for quickly previewing a PDF's extracted text.
- `POST /api/ingest/upload` — the real pipeline: extract text → `detect_paper_type()` → `extract_paper()` → insert into MongoDB. This is what the frontend's upload page actually calls. Accepts `file` (PDF) and optional `link` (used as a fallback if Claude doesn't extract one). Returns `{paper_id, paper_type, data}`.

Dataset handling during ingest: each entry in the extracted `datasets` array is deduplicated by `dataset_name` — if a dataset with that name already exists, the new `paper_id` is added to its `paper_ids` via `$addToSet`; otherwise a new dataset document is inserted. The paper document itself stores only a flat list of dataset name strings under `datasets`, not the full sub-documents.

### Claude service (`app/services/claude_service.py`)

Single file containing all Anthropic SDK calls. Three-stage pipeline:

1. **`detect_paper_type(text)`** — sends first 3000 chars to `classify_paper` tool; returns `"empirical"`, `"survey"`, or `"theoretical"`
2. **`extract_paper(text, paper_type)`** — sends up to 15,000 chars to the matching extraction tool (`EMPIRICAL_TOOL` / `SURVEY_TOOL` / `THEORETICAL_TOOL`); uses prompt caching on the system prompt; returns a dict ready for MongoDB
3. **`compare_papers(paper_docs, dimensions)`** — takes MongoDB documents and generates a structured side-by-side comparison via `COMPARE_TOOL`

Q&A functions:

- **`ask_question()`** — single-turn, returns `{answer, citations, latency_ms, tokens}`
- **`ask_question_stream()`** — SSE streaming generator; yields `citations` event first, then `token` events, then `done`

All tool definitions are plain dicts at module level. The extraction tools have a strict schema: `required: ["name", "authors"]` only — all other fields are optional and Claude omits them if not found in the paper.

### Database (`app/database.py`)

Motor async client initialized at import time. Two collections exposed as module-level globals:

- `papers` — paper documents with type-specific fields
- `datasets` — dataset sub-documents (referenced from empirical papers)

### PDF service (`app/services/pdf_service.py`)

Uses PyMuPDF (`fitz`) to extract text. `split_sections()` locates standard section headings via regex and slices the text — returns normalized keys: `abstract`, `introduction`, `methodology`, `results`, `conclusion`.

### Routes

- `app/routes/upload.py` — `POST /api/upload` (text extraction + preview only)
- `app/routes/ingest.py` — `POST /api/ingest/upload` (full extract → classify → save pipeline)
- `app/routes/papers.py` — `GET /api/papers` (list, optional `paper_type` filter), `GET /api/papers/search` (MongoDB `$text` search, optional `paper_type` filter), `GET /api/papers/datasets/all`, `GET /api/papers/{paper_id}`, `DELETE /api/papers/{paper_id}` (also pulls the deleted paper_id out of any dataset's `paper_ids`)
- `app/routes/ask.py` — `POST /api/ask`, `POST /api/ask/stream` (RAG Q&A over stored papers)
- `app/routes/compare.py` — `POST /api/compare` (structured multi-paper comparison)

Route ordering matters in `papers.py`: `/search` and `/datasets/all` must be registered before the catch-all `/{paper_id}`, since FastAPI matches in registration order and `/search` would otherwise be swallowed as `paper_id="search"`.

## Model Usage

All Claude calls use `claude-sonnet-4-6`. The extraction call uses prompt caching (`cache_control: ephemeral`) on the system prompt to reduce cost on repeated extractions.
