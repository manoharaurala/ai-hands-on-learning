import gradio as gr

from summarizer import summarize

gr.Interface(
    fn=summarize,  # your function
    inputs=gr.Textbox(label="Website URL"),
    outputs=gr.Markdown(label="Summary"),
    title="🔎 Ruby AI Website Summarizer",
).launch(share=False)  # share=True → a public link you can post! 🎉
