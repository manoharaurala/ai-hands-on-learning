# ScalerGPT

ScalerGPT is a containerized Retrieval-Augmented Generation (RAG) service. It indexes Markdown and text notes in ChromaDB, retrieves relevant chunks for a question, and uses OpenAI to generate an answer grounded in that context.

## Architecture

```text
Client
  |
  | HTTP :8000
  v
FastAPI app (app)
  |                 \
  | Chroma HTTP :8000 \\ OpenAI API
  v
Chroma service
  |
  v
Persistent Docker volume
```

- `app.py` exposes the health check and question-answering endpoints.
- `ingest.py` reads `docs/*.md` and `docs/*.txt`, then upserts chunks into the `notes` collection.
- Chroma runs as a separate service and persists data in the `chroma_data` volume.
- OpenAI provides embeddings and chat completions.

## Project Structure

```text
ScalerGPT/
├── app.py
├── ingest.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── compose-and-volumes.md
│   ├── docker-basics.md
│   └── rag-notes.md
└── README.md
```

## Prerequisites

- Docker Desktop
- An OpenAI API key

Docker Compose is the recommended way to run the complete application because it starts both the FastAPI and Chroma services.

## Configure Secrets

Create a local `.env` file from the safe template:

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholder with your real key:

```env
OPENAI_API_KEY=your_real_openai_api_key
```

Never commit `.env` or place a real API key in source code. The `.env.example` file is safe to commit and contains placeholders only.

## Start the Services

Run these commands from the `FifthClass/ScalerGPT` directory:

```bash
docker compose up --build -d
```

Check the service status:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f app
```

The API is available at:

```text
http://localhost:8000
```

Chroma is published on host port `8001` for local inspection, while the app reaches it internally as `http://chroma:8000`.

## Ingest Documents

The repository includes sample notes in `docs/`. Ingest them after the services are running:

```bash
docker compose exec app python ingest.py
```

The command is safe to run again because ingestion uses Chroma `upsert` operations.

To add your own content, place `.md` or `.txt` files in `docs/`, then run the ingestion command again.

## Use the API

Health check:

```bash
curl http://localhost:8000/
```

Ask a question:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What is RAG?"}'
```

The response contains the question, the generated answer, and the number of retrieved source chunks:

```json
{
  "question": "What is RAG?",
  "answer": "...",
  "sources_used": 3
}
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

## Stop the Services

Stop and remove the containers while keeping the Chroma volume:

```bash
docker compose down
```

Remove the containers and permanently delete indexed data:

```bash
docker compose down -v
```

## Useful Docker Commands

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f chroma
docker compose exec app sh
docker compose exec chroma sh
docker compose restart app
docker compose down
```

## Local Python Development

The application expects a running Chroma server, so Docker Compose is the simplest local setup. If you still need a local virtual environment:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Set these variables before running scripts outside Docker:

```bash
export OPENAI_API_KEY="your_real_openai_api_key"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8001"
```

Then run ingestion from this directory:

```bash
python ingest.py
```

Run the API locally:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Troubleshooting

- If Docker cannot connect to its API, start Docker Desktop and retry.
- If the app reports that Chroma is unreachable, check `docker compose ps` and `docker compose logs chroma`.
- If `/ask` returns `No documents indexed`, run `docker compose exec app python ingest.py`.
- If authentication fails, check that `.env` contains a valid `OPENAI_API_KEY`.
- If you change the dependency versions, rebuild with `docker compose up --build -d`.

## Further Reading

- [RAG notes](docs/rag-notes.md)
- [Docker basics](docs/docker-basics.md)
- [Compose and volumes](docs/compose-and-volumes.md)
