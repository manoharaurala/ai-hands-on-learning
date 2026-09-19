import glob
import os
import time
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not API_KEY or API_KEY.startswith("your_"):
    raise RuntimeError("OPENAI_API_KEY is missing or still a placeholder")

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY,
    model_name="text-embedding-3-small",
)

chroma_host = os.getenv("CHROMA_HOST", "localhost")
chroma_port = int(os.getenv("CHROMA_PORT", "8000"))


chroma = None
for attempt in range(1, 11):
    try:
        chroma = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        chroma.heartbeat()
        break
    except Exception:
        print(f"[ingest] Waiting for Chroma ({attempt}/10)...", flush=True)
        time.sleep(2)
if chroma is None:
    raise RuntimeError(
        f"Could not reach Chroma at {chroma_host}:{chroma_port}"
    )

collection = chroma.get_or_create_collection(
    name="notes",
    embedding_function=openai_ef,
)

files = sorted(
    glob.glob(str(Path("docs") / "*.txt"))
    + glob.glob(str(Path("docs") / "*.md"))
)
if not files:
    raise FileNotFoundError(
        "No files found in docs/. Add .txt or .md notes first."
    )

ids, documents, metadatas = [], [], []
for path in files:
    text = Path(path).read_text(encoding="utf-8").strip()

    chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 40]

    for i, chunk in enumerate(chunks):
        ids.append(f"{os.path.basename(path)}::{i}")
        documents.append(chunk)
        metadatas.append({"source": os.path.basename(path)})

if not documents:
    raise ValueError("Files found but no usable chunks.")

collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

print(f"Ingested {len(documents)} chunks from {len(files)} file(s).")
print(f"Collection now holds {collection.count()} chunks total.")
