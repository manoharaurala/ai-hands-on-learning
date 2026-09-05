import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


def get_api_key(name):
    api_key = os.getenv(name)
    if not api_key:
        raise RuntimeError(f"{name} is not set in {ENV_PATH}")
    return api_key
