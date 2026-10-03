from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"

docs = [
    "Our return policy allows refunds within 30 days of purchase.",
    "Shipping is free for orders above ₹999 across India.",
    "For corporate orders above 50 units, contact sales@example.com.",
    "Our office is in Indiranagar, Bangalore. Open Mon-Fri 10am-7pm.",
]

splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
chunks = splitter.create_documents(docs)

embedder = OpenAIEmbeddings(model="text-embedding-3-small")

db = Chroma.from_documents(
    chunks,
    embedder,
    persist_directory=str(CHROMA_DIR),
)

print(f"Indexed {len(chunks)} chunks.")