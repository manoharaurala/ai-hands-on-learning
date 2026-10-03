from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

load_dotenv()

# ⑤ open the same vector store we built in step 1
embedder = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma(persist_directory="./chroma_db", embedding_function=embedder)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ⑥ the prompt: instructions + chunks + question
prompt = ChatPromptTemplate.from_template("""
Answer the question using ONLY the context below. If the context doesn't contain
the answer, say "I don't know." Be concise and quote facts directly.

Context:
{context}

Question: {question}
""")


def rag_answer(question: str):
    chunks = db.similarity_search(question, k=3)
    context = "\n\n".join(chunk.page_content for chunk in chunks)
    chain = prompt | model
    return chain.invoke({"context": context, "question": question}).content


print(rag_answer("Describe My favorite pet."))
print(rag_answer("What is the name of the grandson?"))
print(rag_answer("What is the name of the dog?"))
