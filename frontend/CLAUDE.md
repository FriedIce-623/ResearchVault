# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ResearchVault frontend — a Next.js 16 (App Router) client for the ResearchVault backend. Lets users upload papers, browse/search a library, ask RAG-style questions over papers, compare papers side-by-side, and browse extracted datasets.

## Development Commands

```bash
npm install
npm run dev     # next dev
npm run build   # next build (typechecks + prerenders)
npm run lint    # eslint . (flat config, ESLint 9)
npm run start   # next start (serve a production build)
```

The backend must be running separately (see `../Backend/CLAUDE.md`) at the URL in `NEXT_PUBLIC_API_URL` (`.env`, defaults to `http://localhost:8000`).

## Architecture

### Backend integration (`lib/api.ts`)

Single file with every `fetch` call to the backend. Notable routes it expects:

- `POST /api/ingest/upload` — real upload+extract+save pipeline (NOT `/api/upload`, which is preview-only on the backend)
- `GET /api/papers`, `GET /api/papers/search`, `GET /api/papers/{id}`, `DELETE /api/papers/{id}`
- `GET /api/papers/datasets/all`
- `POST /api/ask`, `POST /api/compare`

If a page 404s against the backend, check the route name here matches what `Backend/app/routes/*.py` actually registers — the two evolve somewhat independently.

### Pages (`app/`)

- `/` (`page.tsx`) — library list with search/type filter, backed by `Paper[]` from `PaperCard`
- `/upload` — drag-drop PDF upload, polls through fake "stage" UI while awaiting the real `uploadPaper()` call
- `/papers/[id]` — full paper detail, renders type-specific sections (empirical/survey/theoretical) based on `paper_type`
- `/compare` — select up to 4 papers, calls `comparePapers()`, renders a table + recharts bar chart for numeric dimensions
- `/datasets` — flat list of extracted datasets
- `/chat` — RAG chat, optionally scoped to selected papers via `?paper=<id>` query param

### Data shape

Most backend documents are typed loosely as `Record<string, unknown>` and cast field-by-field at render time (fields are optional/absent depending on `paper_type`). Any `unknown && <JSX>` conditional must be wrapped in `Boolean(...)` — TypeScript infers the whole logical-AND expression as `unknown` otherwise, which fails `next build`'s typecheck even though it looks fine in isolated files (the IDE's live diagnostics only cover open files; always run `npm run build` to catch this project-wide).

`components/PaperCard.tsx` exports the one strongly-typed shape (`Paper`) — pages that render a list of papers should type their state as `Paper[]`, not `Record<string, unknown>[]`, or `<PaperCard paper={p} />` won't typecheck.

## Known environment gotcha

`next.config.mjs` pins `turbopack.root` to the project directory. Without it, Turbopack's workspace-root auto-detection can walk up to a stray `package.json`/`node_modules` in a parent directory (e.g. an unrelated project accidentally installed into `~`) and pull in a second copy of React, which crashes prerendering with `Cannot read properties of null (reading 'useState')`. If that error reappears, check for stray lockfiles above this directory before assuming it's a code bug.

## Linting

Next.js 16 removed the `next lint` command entirely — `npm run lint` runs `eslint .` directly against `eslint.config.mjs` (flat config, ESLint 9), importing `eslint-config-next/core-web-vitals` and `eslint-config-next/typescript` directly rather than through `FlatCompat` legacy `.extends()` (the latter throws `Converting circular structure to JSON` with `eslint-plugin-react-hooks@7`, which ships flat-only configs).
