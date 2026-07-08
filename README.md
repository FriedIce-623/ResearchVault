# ResearchVault

AI-powered research paper analyser. Upload PDFs, extract structured metadata automatically, chat with your paper library, and compare papers side by side.

Built with FastAPI, Next.js 14, MongoDB, ChromaDB, and the Claude API.

---

## Features

- **Auto-extraction** — upload a PDF and Claude extracts all metadata: authors, architecture, datasets, metrics, results, limitations, and more
- **Paper type detection** — automatically classifies papers as empirical, survey, or theoretical and applies the right schema
- **RAG chatbot** — ask natural language questions across your entire library with cited, section-level answers
- **Paper comparison** — compare 2–4 papers (or all papers at once) across architecture, techniques, metrics, and results with a side-by-side table and bar chart
- **Dataset tracking** — datasets are extracted and stored separately, linked to the papers that use them
- **Semantic search** — search papers by description using embedding-based retrieval

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI, Python 3.10, motor (async MongoDB) |
| Database | MongoDB Atlas |
| Vector store | ChromaDB + sentence-transformers (all-MiniLM-L6-v2) |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| PDF parsing | PyMuPDF |
| Package manager | uv (backend), npm (frontend) |

---

## Project structure

```
ResearchVault/
├── Backend/
│   ├── app/
│   │   ├── models/          # Pydantic schemas
│   │   ├── routes/          # FastAPI routers (ask, compare, ingest, papers)
│   │   ├── services/        # claude_service.py — all Claude API logic
│   │   ├── database.py      # MongoDB motor connection
│   │   ├── embeddings.py    # ChromaDB + sentence-transformers
│   │   └── main.py          # FastAPI app entry point
│   ├── .env                 # API keys (never commit this)
│   └── pyproject.toml
└── frontend/
    ├── app/                 # Next.js App Router pages
    │   ├── page.tsx         # Library
    │   ├── upload/          # Upload page
    │   ├── papers/[id]/     # Paper detail
    │   ├── chat/            # RAG chatbot
    │   ├── compare/         # Paper comparison
    │   └── datasets/        # Dataset browser
    ├── components/          # Sidebar, PaperCard
    ├── lib/api.ts           # Typed fetch functions
    └── .env.local           # Frontend env (never commit this)
```

---

## Local setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- uv (`pip install uv`)
- MongoDB Atlas account (free tier works)
- Anthropic API key

### 1. Clone the repo

```bash
git clone https://github.com/FriedIce-623/ResearchVault.git
cd ResearchVault
```

### 2. Backend setup

```bash
cd Backend
uv venv
uv sync
```

Create `Backend/.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
MONGODB_URI=mongodb+srv://your-connection-string
DATABASE_NAME=researchvault
```

Run the backend:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

Test it:
```bash
curl http://localhost:8000/health
# → {"status":"ok","papers":0,"datasets":0}
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the frontend:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Backend health check |
| POST | `/api/ingest/upload` | Upload and extract a PDF |
| GET | `/api/papers` | List all papers |
| GET | `/api/papers/search?q=` | Semantic search |
| GET | `/api/papers/{paper_id}` | Get paper by ID |
| PATCH | `/api/papers/{paper_id}` | Update paper fields |
| DELETE | `/api/papers/{paper_id}` | Delete paper |
| GET | `/api/papers/datasets/all` | List all datasets |
| POST | `/api/ask` | Ask a question (RAG) |
| POST | `/api/ask/stream` | Streaming answer |
| POST | `/api/compare` | Compare papers |

---

## Paper schemas

Fields vary by paper type. All types share: `paper_id`, `name`, `authors`, `doi`, `link`, `date_of_publication`, `code_link`, `key_insights`, `limitations`, `metrics_used`, `results`.

**Empirical** adds: `architecture`, `key_techniques`, `preprocessing`, `training_strategy`, `dataset_ids`

**Survey** adds: `papers_surveyed`, `taxonomy`, `research_gaps`, `time_period_covered`

**Theoretical** adds: `propositions`, `proofs_or_derivations`, `assumptions`, `applicability`

**Dataset** schema: `dataset_id`, `dataset_name`, `paper_ids`, `public`, `samples`, `support`, `classes`, `task`, `modality`, `link`, `key_insights`

---

## Environment variables

### Backend (`Backend/.env`)
| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `DATABASE_NAME` | MongoDB database name (e.g. `researchvault`) |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL (e.g. `http://localhost:8000` locally, your Render URL in production) |

---

## Deployment

Frontend is deployed on Vercel. Backend is deployed on Render.

See the repo for deployment configuration.

---

## Notes

- First PDF upload takes ~30 seconds extra — sentence-transformers downloads its model (~90MB) once and caches it
- Compare all caps at 20 papers to stay within Claude's context window
- ChromaDB persists to `Backend/chroma_db/` on disk — this folder is gitignored
