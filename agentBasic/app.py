import gradio as gr

try:
    from .agent import agent
except ImportError:
    from agent import agent


def chat(user_message, history):
    return agent(user_message, history)


gr.ChatInterface(fn=chat, title="🛍️ Smart Shop Assistant").launch(share=False)
