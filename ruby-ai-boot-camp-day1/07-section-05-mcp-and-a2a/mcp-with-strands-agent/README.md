# Strands Agents with MCP Servers

These scripts connect Strands Agents to MCP servers over stdio. The agent
discovers the server's tools at runtime and then uses them to answer the
question.

## Files

| Script | MCP server | Model provider |
| --- | --- | --- |
| `agent_with_local_mcp.py` | Local weather server in `../mcp-basics/server.py` | Bedrock |
| `agent_with_aws_docs_mcp.py` | AWS Documentation MCP server via `uvx` | Bedrock |
| `agent_with_local_mcp_groq.py` | Local weather server in `../mcp-basics/server.py` | Groq |
| `agent_with_aws_docs_mcp_groq.py` | AWS Documentation MCP server via `uvx` | Groq |

## Install

For Bedrock:

```bash
python -m pip install -r requirements.txt
```

For Groq:

```bash
python -m pip install -r requirements-groq.txt
```

The AWS Documentation scripts require `uvx`. Install `uv` separately if it is
not already available:

```bash
python -m pip install uv
```

## Configure Bedrock

Create `.env` from `.env.example` and set:

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
```

Configure AWS credentials with the AWS CLI, an AWS profile, or the standard
AWS environment variables. Bedrock model access must be enabled in the
selected region.

Run:

```bash
python agent_with_local_mcp.py
python agent_with_aws_docs_mcp.py
```

The AWS Documentation MCP server is downloaded on its first run by `uvx`.

## Configure Groq

Set these variables in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_ID=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Run:

```bash
python agent_with_local_mcp_groq.py
python agent_with_aws_docs_mcp_groq.py
```

The AWS Documentation Groq script still needs `uvx`, but it does not need
Bedrock access. AWS credentials are not required unless the MCP server or
another tool explicitly uses them.

## How the MCP flow works

1. `MCPClient` starts the server over stdio.
2. The client discovers the server's tools.
3. Strands gives those tools to the agent.
4. The agent calls the appropriate MCP tool and returns an answer with sources
   when using the AWS Documentation server.

Never commit `.env`, API keys, AWS credentials, or generated files.
