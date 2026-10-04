# RubyGPT

RubyGPT is a Dockerized FastAPI RAG service. It stores document embeddings in
ChromaDB, retrieves relevant notes, and uses OpenAI to answer questions from
those notes.

## Run locally

Run these commands from the `rubygpt/` directory:

```bash
cp .env.example .env         # then put your REAL key inside .env

docker compose up -d --build

docker compose ps -a
docker compose logs app

docker compose exec app python ingest.py

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Docker?"}'

docker compose down
docker compose up -d
curl http://localhost:8000/

docker compose down -v
```

Add `.txt` or `.md` source documents to `docs/` before running the ingestion
command. The ingestion command chunks those files and stores their embeddings
in the ChromaDB service.

## Environment variables

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` to a valid key. Never
commit `.env` or place an API key directly in source code, Dockerfiles, or
compose files.

The API is available at `http://localhost:8000`. ChromaDB is available from
the host at `http://localhost:8001`, while the application connects to it
internally on port `8000`.
