# LLM Reliability Demonstrations

This folder contains four small experiments that test how prompt design and
tool design affect the reliability of an LLM application. Each experiment
uses repeated calls to `gpt-4o-mini`, scores the results, and prints a summary
so that conclusions are based on observed distributions rather than one
response.

## Demonstrations

### 1. Chain-of-Thought vs. direct answers

`cot_vs_direct.py` runs multi-step spatial, relational, scheduling, inventory,
and logic problems with two prompt strategies:

- **Direct:** request only a short final answer.
- **Chain-of-thought:** request intermediate steps followed by a final answer.

It compares accuracy and latency across repeated runs. The significance is
that intermediate steps can make multi-step reasoning more reliable, but the
experiment also exposes the trade-off in response length and latency. It is
intended for a non-reasoning model so the prompt difference remains measurable.

### 2. Unconstrained output vs. JSON prompting vs. schema enforcement

`structured_output.py` extracts sentiment and entities from the same customer
review using three strategies:

1. No output constraint.
2. A prompt asking for JSON.
3. An API-enforced JSON schema.

Every result is passed through a strict downstream parser. The experiment
measures response variation, JSON parse rate, and schema-match rate. Its
significance is practical: a response can be semantically correct for a
person but still unusable to software. API-level structure is a stronger
reliability guarantee than instructions alone.

The sample outputs are recorded in:

- `output-a-unconstrained.md`
- `output-b-prompt-json.md`
- `output-c-schema.md`

### 3. Tool-call error injection and handling

`tool_error_handling.py` simulates a weather tool whose second call returns an HTTP
503. It compares:

- A normal assistant prompt with no error guidance.
- A prompt requiring explicit error reporting and prohibiting guesses.
- A no-tool control question.

The experiment scores whether the model acknowledges the failure, reports the
error detail, or fabricates weather data for the failed city. This matters
because a tool failure does not automatically produce a transparent assistant
response. Fabricated data is a production incident, while explicit error
reporting makes a degraded response diagnosable and safer.

### 4. Tool name and description calibration

`tool_schema_calibration.py` tests weather-tool routing across a 2x2 matrix:

| Tool names | Loose descriptions | Tight descriptions |
| --- | --- | --- |
| Descriptive | A | B |
| Opaque | C | D |

Tool choice is forced, so the experiment isolates *which* tool the model
selects. The results attribute routing accuracy to the tool name, the
description, or both. This is significant for production tool registries and
MCP servers: descriptive names may hide weak descriptions, while generic
names make precise descriptions load-bearing.

## Running the demonstrations

From the repository root, install the shared dependencies and set the API key
in a local `.env` file:

```bash
python -m pip install -r requirements.txt
export OPENAI_API_KEY="your_api_key_here"
```

Then run an experiment:

```bash
python llm-reliability-demos/cot_vs_direct.py
python llm-reliability-demos/structured_output.py
python llm-reliability-demos/tool_error_handling.py
python llm-reliability-demos/tool_schema_calibration.py
```

The `.env` file is ignored by Git and must never be committed. These
experiments make live API calls, so running them consumes API quota and
results can vary with model or service changes.
