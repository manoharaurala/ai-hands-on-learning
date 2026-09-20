# Sycophancy Benchmark

This project measures whether a model changes a correct answer after escalating
social pressure. It supports OpenAI and Gemini.

## Setup

Run these commands from the `sycophancy` directory.

### macOS/Linux

Because the workspace path contains `:`, create the virtual environment in
`/tmp`:

```bash
python3 -m venv /tmp/scaler-sycophancy-venv
source /tmp/scaler-sycophancy-venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create a local environment file from the safe template:

```bash
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead. Edit `.env`
and set the key for the provider you want to test. Never commit or share `.env`.

For Gemini, set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`. The legacy
`GOOGLE_API_KEY` name is also accepted.

## Run

With the virtual environment active:

```bash
python openai_sycophancy_benchmark.py
python gemini_sycophancy_benchmark.py
```

`openai_sycophancy_benchmark.py` always uses OpenAI, and
`gemini_sycophancy_benchmark.py` always uses Gemini.
Both launch `sycophancy_benchmark.py`.

For Gemini, use this `.env` configuration:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash
```

To test each provider separately without running the benchmark:

```bash
python openai_api_test.py
python gemini_api_test.py
```

The benchmark writes charts using a non-interactive Matplotlib backend. The
provider and model are selected from `.env`.

## Deactivate

```bash
deactivate
```