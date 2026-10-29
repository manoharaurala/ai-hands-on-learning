# Section 2 — Giving Agents Tools

These notebooks show how agents use custom functions, prebuilt tools, AWS
service tools, class-based tools, and asynchronous tools.

## Files

| Notebook | What it covers | Provider |
| --- | --- | --- |
| `01_building_tools.ipynb` | Custom tools: calculations, sales analysis, and inventory checks | Bedrock |
| `02_prebuilt_and_aws_tools.ipynb` | Calculator, HTTP, file-writing, and AWS service tools | Bedrock |
| `03_advanced_tool_patterns.ipynb` | Class-based tools and parallel asynchronous tools | Bedrock |
| `01_building_tools_groq.ipynb` | Custom tools using a Groq model | Groq |
| `02_prebuilt_and_aws_tools_groq.ipynb` | Prebuilt tools and AWS service tools using Groq | Groq |
| `03_advanced_tool_patterns_groq.ipynb` | Advanced and parallel tools using Groq | Groq |

## Install

For Bedrock notebooks:

```bash
python -m pip install -r requirements.txt
```

For Groq notebooks:

```bash
python -m pip install -r requirements-groq.txt
```

## Configure Bedrock

Create `.env` from `.env.example` and set:

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
```

Configure AWS credentials with the AWS CLI, an AWS profile, or the standard
AWS environment variables. The AWS tools notebook also requires permissions
for the S3, DynamoDB, and Lambda operations it demonstrates.

Run:

```bash
jupyter lab 01_building_tools.ipynb
jupyter lab 02_prebuilt_and_aws_tools.ipynb
jupyter lab 03_advanced_tool_patterns.ipynb
```

Notebook 2 creates temporary S3, DynamoDB, and Lambda resources for its demo
and attempts to clean them up in the final cells. Review the cells and AWS
permissions before running it.

## Configure Groq

Set these variables in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_ID=openai/gpt-oss-120b
GROQ_PARALLEL_MODEL_ID=qwen/qwen3.8-27b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Run the `_groq` notebooks with the same `jupyter lab` commands, replacing the
filename with its `_groq` counterpart.

The Groq AWS-tools notebook still calls AWS services, so it requires AWS
credentials and permissions even though its language model runs through Groq.

## Generated files and security

The notebooks may create local files such as `inventory_demo.db` and
`weather_summary.txt`. Never commit `.env`, API keys, AWS credentials, or
other generated files.
