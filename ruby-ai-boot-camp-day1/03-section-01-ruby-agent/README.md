# Section 1 — Your First AI Agent

This section builds the same small agent with Strands Agents and
LangChain/LangGraph. The Bedrock files use Amazon Nova Lite; the `_groq`
files use Groq's OpenAI-compatible API.

## Files

| File | Purpose | Provider |
| --- | --- | --- |
| `01_hello_agent.ipynb` | Walkthrough: model, agent, custom tool, built-in calculator | Bedrock |
| `hello_agent.py` | Minimal Strands agent | Bedrock |
| `hello_langgraph_agent.py` | LangChain/LangGraph agent with one tool | Bedrock |
| `01_hello_agent_groq.ipynb` | Notebook version using Groq | Groq |
| `hello_agent_groq.py` | Strands agent using Groq | Groq |
| `hello_langgraph_agent_groq.py` | LangChain/LangGraph agent using Groq | Groq |

## Install

For Bedrock:

```bash
python -m pip install -r requirements.txt
```

For Groq:

```bash
python -m pip install -r requirements-groq.txt
```

## Configure Bedrock

Create `.env` from `.env.example` and set:

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
```

Configure AWS credentials using the AWS CLI, an AWS profile, or the standard
AWS environment variables. The Bedrock model must be enabled in the selected
AWS region.

Run:

```bash
python hello_agent.py
python hello_langgraph_agent.py
jupyter lab 01_hello_agent.ipynb
```

## Configure Groq

Set these variables in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_ID=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Run:

```bash
python hello_agent_groq.py
python hello_langgraph_agent_groq.py
jupyter lab 01_hello_agent_groq.ipynb
```

## Optional LangSmith tracing

Set the following in `.env`:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=section-01-ruby-agent
```

Never commit `.env` or real API keys.
