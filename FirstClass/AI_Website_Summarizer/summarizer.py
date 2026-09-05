from openai import OpenAI
from util.scraper import fetch_website_contents
from util.config import get_api_key

api_key = get_api_key("OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.openai.com/v1",
)

system_prompt = """You analyze the contents of a website and
give a short, friendly summary. Ignore navigation menus.
Respond in markdown."""


def summarize(url):
    website = fetch_website_contents(url)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Summarize this website:\n\n{website}"},
        ],
    )
    return response.choices[0].message.content
