import os
import time

import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI(title="ScalerGPT")

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not API_KEY or API_KEY.startswith("your_"):
    raise RuntimeError("OPENAI_API_KEY is missing or still a placeholder")

llm = OpenAI(api_key=API_KEY)

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY,
    model_name="text-embedding-3-small",
)

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))


def connect_to_chroma(retries: int = 30, delay: int = 2):
    for attempt in range(1, retries + 1):
        try:
            client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            client.heartbeat()
            print(
                f"[ScalerGPT] Connected to Chroma at "
                f"{CHROMA_HOST}:{CHROMA_PORT}",
                flush=True,
            )
            return client
        except Exception as error:
            print(
                f"[ScalerGPT] Waiting for Chroma "
                f"({attempt}/{retries}): {type(error).__name__}",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError(
        f"Could not reach Chroma at {CHROMA_HOST}:{CHROMA_PORT}"
    )


chroma = connect_to_chroma()
collection = chroma.get_or_create_collection(
    name="notes",
    embedding_function=openai_ef,
)


class Question(BaseModel):
    query: str


@app.get("/")
def health():
    return {
        "status": "ScalerGPT is live",
        "docs_indexed": collection.count(),
        "chroma_host": CHROMA_HOST,
        "chroma_port": CHROMA_PORT,
    }


@app.post("/ask")
def ask(q: Question):
    if collection.count() == 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "No documents indexed. Run: "
                "docker compose exec app python ingest.py"
            ),
        )
    hits = collection.query(query_texts=[q.query], n_results=3)
    documents = hits.get("documents") or [[]]
    context = "\n\n---\n\n".join(documents[0])
    system_prompt = (
        "You are ScalerGPT, a helpful teaching assistant. "
        "Answer using ONLY the context below. If it does not contain the answer, "
        "say you don't know.\n\n"
        f"CONTEXT:\n{context}"
    )
    response = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": q.query},
        ],
    )
    return {
        "question": q.query,
        "answer": response.choices[0].message.content,
        "sources_used": len(documents[0]),
    }