from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from sentence_transformers import CrossEncoder

from FourthClass.RagDemo.rerank import RERANKER_MODEL, rerank_documents
from util.config import get_api_key


CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
CANDIDATE_K = 25
FINAL_K = 3

embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory=str(CHROMA_DIR), embedding_function=embedder)
reranker = CrossEncoder(RERANKER_MODEL)
model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=get_api_key("OPENAI_API_KEY"),
)

prompt = ChatPromptTemplate.from_template(
    """
Answer the question using ONLY the context below. If the context doesn't contain
the answer, say "I don't know." Be concise and quote facts directly.

Context:
{context}

Question: {question}
"""
)


def rag_answer(question: str) -> str:
    candidates = db.similarity_search(question, k=CANDIDATE_K)
    chunks = rerank_documents(question, candidates, reranker, top_k=FINAL_K)
    context = "\n\n".join(c.page_content for c in chunks)
    response = (prompt | model).invoke(
        {"context": context, "question": question}
    )
    return response.content


if __name__ == "__main__":
    print(rag_answer("How long do I have to return something?"))