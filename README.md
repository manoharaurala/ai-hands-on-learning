# AI Hands-On Learning

This repository contains Python exercises and examples created during the AI learning classes. Each class is kept in its own folder so new class material can be added without changing the shared project setup.

## Project structure

```text
Code/
├── .env                         # Local API keys; never commit this file
├── requirements.txt
├── FirstClass/                  # Class exercises
├── SecondClass/                 # Class exercises
├── util/                        # Shared utility modules
└── ...                          # Additional class folders
```

## Setup

### 1. Create the virtual environment

The workspace path contains `:`, so create the virtual environment outside the project folder:

```bash
python3 -m venv /tmp/scaler-code-venv
```

### 2. Activate the virtual environment

From the `Code` folder:

```bash
source /tmp/scaler-code-venv/bin/activate
```

### 3. Install the packages

```bash
python -m pip install -r requirements.txt
```

You only need to install the packages once, unless `requirements.txt` changes.

### 4. Configure environment variables

Create `.env` directly inside the `Code` folder:

```env
OPENAI_API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_key_here
```

Only add the variables required by the class you are running. Do not commit `.env` or share API keys.

## Run a class exercise

From the `Code` folder, run any Python file by providing its path:

```bash
python FirstClass/first_call.py
python FirstClass/AI_Website_Summarizer/app.py
```

For a class that imports shared modules, run it from the repository root with `-m`:

```bash
python -m SecondClass.summarizer_langchain
python -m SecondClass.memory_demo
python -m SecondClass.app
```

For a folder-based app, run its entry-point file from the project root so imports resolve correctly:

```bash
python FirstClass/AI_Website_Summarizer/arena_app.py
```

## Add a new class

Create a new folder at the repository root and place that class's Python files inside it:

```text
ThirdClass/
├── example.py
└── notes.md
```

Reuse the root `requirements.txt` and `.env` unless the class needs an additional dependency or environment variable.

## Deactivate the virtual environment

```bash
deactivate
```

## Run without activation

You can also run a file directly with the virtual environment interpreter:

```bash
/tmp/scaler-code-venv/bin/python FirstClass/first_call.py
```

## VS Code interpreter

In VS Code, open the Command Palette with `Cmd+Shift+P`, choose **Python: Select Interpreter**, and select:

```text
/tmp/scaler-code-venv/bin/python
```
