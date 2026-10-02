import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-4o-mini",
    instructions="You are a witty travel guide.",
    input="Suggest one thing to do in Bangalore.",
)

print(response.output_text)
