"""Make a minimal OpenAI API request to verify local configuration."""

import os

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI


load_dotenv(find_dotenv())


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set in .env")

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input="Reply with the word OK.",
        max_output_tokens=10,
    )
    print(f"OpenAI API check passed: {response.output_text.strip()}")


if __name__ == "__main__":
    main()
