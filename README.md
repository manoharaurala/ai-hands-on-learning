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

Run this command from the `Code` folder:

```bash
python -m pip install -r requirements.txt
```

You only need to install the packages once, unless `requirements.txt` changes.

For an exercise with its own dependency file, such as `basic`, install that
file explicitly:

```bash
python -m pip install -r basic/requirements.txt
```

### 4. Configure environment variables

Create `.env` directly inside the `Code` folder:

```env
OPENAI_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_gemini_key_here
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

## Repair or recreate a broken pip environment

If `python -m pip` reports that `pip` has no `__main__` module, repair pip
inside the activated environment:

```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel
```

If that does not work, delete only the virtual environment and recreate it.
First deactivate it, then run:

```bash
deactivate
rm -rf /tmp/scaler-code-venv
python3 -m venv /tmp/scaler-code-venv
source /tmp/scaler-code-venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

The `rm -rf` command above targets only `/tmp/scaler-code-venv`. Do not
replace that path with the project path or another directory. If you created
the environment somewhere else, substitute only the exact virtual-environment
directory you want to remove.

Verify that Python and pip use the recreated environment:

```bash
which python
python -m pip --version
```

Both commands should reference `/tmp/scaler-code-venv`.

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
