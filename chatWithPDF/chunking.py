from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder


@dataclass
class PDFIndex:
    vector_store: Chroma
    chunks: list
    bm25: BM25Okapi
    reranker: CrossEncoder

    def retrieve(self, question, candidate_count=8, result_count=4):
        dense = self.vector_store.similarity_search(question, k=candidate_count)
        lexical = self.bm25.get_top_n(
            question.lower().split(), self.chunks, n=candidate_count
        )

        ranked = {}
        for rank, document in enumerate(dense + lexical):
            key = (document.metadata.get("page"), document.page_content)
            ranked.setdefault(key, {"document": document, "score": 0.0})
            ranked[key]["score"] += 1 / (rank + 1)

        candidates = [
            item["document"]
            for item in sorted(
                ranked.values(), key=lambda item: item["score"], reverse=True
            )
        ]
        pairs = [(question, document.page_content) for document in candidates]
        reranked = sorted(
            zip(self.reranker.predict(pairs), candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        return [document for _, document in reranked[:result_count]]


def build_index(pdf_path):
    pages = PyPDFLoader(pdf_path).load()  # ① read all pages
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_documents(pages)  # ② chunk them
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    db = Chroma.from_documents(chunks, embedder)  # ③ in-memory store
    bm25 = BM25Okapi([chunk.page_content.lower().split() for chunk in chunks])
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return PDFIndex(db, chunks, bm25, reranker)
