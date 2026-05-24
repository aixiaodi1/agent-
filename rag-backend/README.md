# RAG Backend

FastAPI backend for local RAG document ingestion.

## Setup

From `rag-backend/`:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Environment

Copy `.env.example` to `.env` and set:

- `EMBEDDING_API_BASE_URL`
- `EMBEDDING_API_KEY` or `MINIMAX_API_KEY`
- `CHROMA_PERSIST_DIR`
- `REDIS_URL`

Secrets stay in `.env`; `.env` is not committed.

Make sure `CHROMA_PERSIST_DIR` points to a local directory that exists or can be created by the backend process, and that the process has permission to write there. The default local data directory is ignored by Git.

## Redis In WSL

```bash
sudo service redis-server start
redis-cli ping
```

If Windows cannot reach WSL Redis through `redis://localhost:6379/0`, run FastAPI and the RQ worker inside WSL.

## Run

Start FastAPI from `rag-backend/`:

```bash
uvicorn app.main:app --reload --port 8000
```

Start the RQ worker from `rag-backend/`:

```bash
rq worker rag-ingestion --url redis://localhost:6379/0
```

Open `http://localhost:8000/admin`.

## Verify

From `rag-backend/`:

```bash
python -m pytest -v
```
