from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ① load your documents (any text — for now, hardcoded)
docs = [
    "My favorite pet is Ruby cat.",
    "It has grandson named Annayya 420",
    "Ruby mischievous and always hungry",
    "She is good in catching mice and loves to play with yarn.",
]

# ② split into chunks (small docs here, but production = thousands of pages)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)

chunks = text_splitter.create_documents(docs)

# ③ use OpenAI's cost-effective embedding model
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# ④ build the vector store from chunks + embeddings (saves to disk)
db = Chroma.from_documents(
    documents=chunks,
    embedding=embedder,
    persist_directory="./chroma_db",
)

print(f"Indexed {len(chunks)} chunks 🎉")
