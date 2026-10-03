from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_template("""
You are a helpful PDF assistant. Answer the question using ONLY the context below.
If the context does not directly answer the question, say exactly:
"I couldn't find that in the document."
Do not infer, guess, or use outside knowledge.
Only include a Sources line when the context directly supports your answer.
When sources are present, list each page only once as:
Sources: page X, page Y.

Context:
{context}

Question: {question}

Conversation history:
{history}
""")


def _history_text(history):
    turns = []
    for turn in history or []:
        if isinstance(turn, dict):
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if isinstance(content, str) and content:
                turns.append(f"{role.title()}: {content}")
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            user_text, assistant_text = turn
            if user_text:
                turns.append(f"User: {user_text}")
            if assistant_text:
                turns.append(f"Assistant: {assistant_text}")
    return "\n".join(turns[-6:])


def ask(question, db, history=None):
    documents = db.retrieve(question)
    pages = {}
    for document in documents:
        page = document.metadata.get("page", 0) + 1
        pages.setdefault(page, []).append(document.page_content)

    context = "\n\n".join(
        f"[page {page}] {' '.join(contents)}"
        for page, contents in pages.items()
    )

    chain = prompt | model
    return chain.invoke(
        {
            "context": context or "No sufficiently relevant passages were found.",
            "question": question,
            "history": _history_text(history),
        }
    ).content
