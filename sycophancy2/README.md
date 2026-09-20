# Prompting Strategy Benchmark

This project compares direct, zero-shot chain-of-thought, and few-shot
chain-of-thought prompting. It reports answer accuracy and token usage for
five questions designed to require multi-step reasoning.

## Setup

Run these commands from the `sycophancy2` directory.

### macOS/Linux

Because the workspace path contains `:`, create the virtual environment in
`/tmp`:

```bash
python3 -m venv /tmp/scaler-sycophancy2-venv
source /tmp/scaler-sycophancy2-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configure OpenAI

Create a local environment file from the safe template:

```bash
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env`. Then edit `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

Never commit `.env` or share API keys. It is excluded by `.gitignore`.

## Run

With the virtual environment active:

```bash
python main.py
```

The benchmark writes `benchmark_results.png` in the current directory. That
generated file is ignored by git.

## Deactivate

```bash
deactivate
```