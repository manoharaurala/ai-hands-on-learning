from typing import Any

import gradio as gr

from FourthClass.RagPDFChat.ask import ask
from FourthClass.RagPDFChat.extract import build_index


state: dict[str, Any] = {"db": None}


def upload(pdf: Any) -> str:
    pdf_path = getattr(pdf, "name", pdf)
    state["db"] = build_index(pdf_path)
    return "PDF indexed. Ask me anything about it."


def chat(message: str, _history: list[dict[str, str]]) -> str:
    if state["db"] is None:
        return "Please upload a PDF first."
    return ask(state["db"], message)


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="Chat with your PDF") as demo:
        gr.Markdown("## Chat with your PDF")
        pdf = gr.File(label="Upload a PDF", file_types=[".pdf"])
        status = gr.Markdown()
        pdf.upload(upload, inputs=pdf, outputs=status)
        gr.ChatInterface(fn=chat)
    return demo
