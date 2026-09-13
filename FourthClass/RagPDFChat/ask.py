from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from util.config import get_api_key


RETRIEVAL_K = 4

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=get_api_key("OPENAI_API_KEY"),
)

prompt = ChatPromptTemplate.from_template(
    """
You are a helpful PDF assistant. Answer the question using ONLY the context below.
If the context doesn't contain the answer, say "I couldn't find that in the document."
After your answer, list the page numbers you used as: Sources: page X, page Y.

Context:
{context}

Question: {question}
"""
)


def ask(db: Chroma, question: str) -> str:
    chunks = db.similarity_search(question, k=RETRIEVAL_K)
    context = "\n\n".join(
        f"[Page {chunk.metadata.get('page', 0) + 1}] {chunk.page_content}"
        for chunk in chunks
    )
    response = (prompt | model).invoke(
        {"context": context, "question": question}
    )
    return response.content
