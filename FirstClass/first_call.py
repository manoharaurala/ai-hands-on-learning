# pip install openai
from openai import OpenAI
from util.config import get_api_key

api_key = get_api_key("OPENAI_API_KEY")

"""
Create the OpenAI client explicitly with the API key and official API URL.
client = OpenAI(
    api_key=api_key,
    base_url="https://api.openai.com/v1",
)
"""
client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a joker"},
        {"role": "user", "content": "Tell me a joke about my cat Ruby."},
    ],
)
print(response.choices[0].message.content)
