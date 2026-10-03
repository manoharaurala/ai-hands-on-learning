import gradio as gr

from chunking import build_index
from ragCitation import ask

state = {"db": None}  # ① remember the index across turns


def upload(pdf):
    state["db"] = build_index(pdf.name)  # ② re-index whenever a new PDF arrives
    return "✅ PDF indexed! Ask me anything about it."


def chat(message, history):
    if state["db"] is None:
        return "Please upload a PDF first 📄"
    return ask(message, state["db"], history)


with gr.Blocks(title="📄 Chat with your PDF") as demo:
    gr.Markdown("## 📄 Chat with your PDF (powered by RAG)")
    pdf = gr.File(label="Upload a PDF", file_types=[".pdf"])
    status = gr.Markdown()
    pdf.upload(upload, inputs=pdf, outputs=status)
    gr.ChatInterface(fn=chat)

demo.launch(share=True)  # share=True → public link!
