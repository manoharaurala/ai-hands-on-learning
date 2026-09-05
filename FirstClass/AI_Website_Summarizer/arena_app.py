# pip install openai gradio python-dotenv
import os
from pathlib import Path

import gradio as gr
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv
from scraper import fetch_website_contents

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(f"OPENAI_API_KEY is not set in {env_path}")

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise RuntimeError(f"GEMINI_API_KEY is not set in {env_path}")

openai_client = OpenAI(
    api_key=api_key,
    base_url="https://api.openai.com/v1",
)
gemini_client = genai.Client(api_key=gemini_api_key)

def ask_openai(prompt):
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    return response.choices[0].message.content

def ask_gemini(prompt):
    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=200),
    )
    return response.text

def battle(url):
    website = fetch_website_contents(url)
    prompt = (
        "Summarize the following webpage in concise markdown. "
        "Include the main topic and the most important points.\n\n"
        f"{website}"
    )
    a = ask_openai(prompt)
    b = ask_gemini(prompt)
    return a, b

def vote(label):
    return f"🗳️ Thanks! You voted: **{label}**"   # in real apps, save this to a file/DB

with gr.Blocks(title="LLM Arena") as demo:
    gr.Markdown("# 🥊 LLM Arena — one prompt, two models")
    prompt = gr.Textbox(label="Website URL to summarize")
    go = gr.Button("⚔️ Battle!", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🤖 OpenAI gpt-4o-mini")
            out_a = gr.Markdown()
            with gr.Row():
                up_a   = gr.Button("👍");  down_a = gr.Button("👎")
        with gr.Column():
            gr.Markdown("### 🤖 Gemini 3.5 Flash-Lite")
            out_b = gr.Markdown()
            with gr.Row():
                up_b   = gr.Button("👍");  down_b = gr.Button("👎")

    verdict = gr.Markdown()

    go.click(battle, inputs=prompt, outputs=[out_a, out_b])
    up_a.click(lambda: vote("👍 Model A"), outputs=verdict)
    down_a.click(lambda: vote("👎 Model A"), outputs=verdict)
    up_b.click(lambda: vote("👍 Model B"), outputs=verdict)
    down_b.click(lambda: vote("👎 Model B"), outputs=verdict)

demo.launch(share=True)   # → local + public link 🎉