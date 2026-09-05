# OpenAI Python Example

## Project files

```text
Code/
├── .env
├── requirements.txt
└── FirstClass/
    └── first_call.py
```

## 1. Create the virtual environment

The workspace path contains `:`, so create the virtual environment outside the project folder:

```bash
python3 -m venv /tmp/scaler-code-venv
```

## 2. Activate the virtual environment

From the `Code` folder:

```bash
source /tmp/scaler-code-venv/bin/activate
```

## 3. Install the packages

```bash
python -m pip install -r requirements.txt
```

You only need to install the packages once, unless `requirements.txt` changes.

## 4. Configure the API key

Create `.env` directly inside the `Code` folder:

```env
OPENAI_API_KEY=your_api_key_here
```

Do not commit `.env` or share your API key.

## 5. Run the code

```bash
python FirstClass/first_call.py
```

## 6. Deactivate the virtual environment

```bash
deactivate
```

## Run without activation

You can also run the script directly with the virtual environment interpreter:

```bash
/tmp/scaler-code-venv/bin/python FirstClass/first_call.py
```

## VS Code interpreter

In VS Code, open the Command Palette with `Cmd+Shift+P`, choose **Python: Select Interpreter**, and select:

```text
/tmp/scaler-code-venv/bin/python
```
