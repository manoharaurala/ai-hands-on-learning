from dotenv import load_dotenv
from openai import OpenAI

from webScraper import fetch_website_contents

load_dotenv()  # <-- this reads your .env file
client = OpenAI()

system_prompt = """You analyze the contents of a website and
give a short, friendly summary. Ignore navigation menus.
Respond in markdown."""


def summarize(url):
    website = fetch_website_contents(url)
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=system_prompt,
        input=f"Summarize this website:\n\n{website}"
    )

    return response.output_text
