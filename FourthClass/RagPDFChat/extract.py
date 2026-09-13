from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def build_index(pdf_path: str | Path) -> Chroma:
    pages = PyPDFLoader(str(pdf_path)).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)
    embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma.from_documents(chunks, embedder)
