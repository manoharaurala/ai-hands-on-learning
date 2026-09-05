# pip install python-dotenv
from dotenv import load_dotenv
# pip install openai
from openai import OpenAI
import os
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set")

"""
Create the OpenAI client explicitly with the API key and official API URL.
client = OpenAI(
    api_key=api_key,
    base_url="https://api.openai.com/v1",
)
"""
client= OpenAI(api_key=api_key,base_url="https://api.openai.com/v1")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a joker"},
        {"role": "user",   "content": "Tell me a joke about my cat Ruby."},
    ],
)
print(response.choices[0].message.content)
