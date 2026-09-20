"""Make a minimal Gemini API request to verify local configuration."""

import os

from dotenv import find_dotenv, load_dotenv
from google import genai


load_dotenv(find_dotenv())


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is not set in .env")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        contents="Reply with the word OK.",
    )
    print(f"Gemini API check passed: {response.text.strip()}")


if __name__ == "__main__":
    main()