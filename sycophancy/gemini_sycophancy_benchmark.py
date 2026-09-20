"""Run the benchmark using Gemini."""

import os
import runpy
from pathlib import Path


os.environ["LLM_PROVIDER"] = "gemini"
runpy.run_path(
	Path(__file__).with_name("sycophancy_benchmark.py"), run_name="__main__"
)
