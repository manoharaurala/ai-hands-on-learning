"""Run the benchmark using OpenAI."""

import os
import runpy
from pathlib import Path


os.environ["LLM_PROVIDER"] = "openai"
runpy.run_path(
	Path(__file__).with_name("sycophancy_benchmark.py"), run_name="__main__"
)
