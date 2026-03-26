
# Tool Calling from Scratch

A learning project that implements LLM tool calling from scratch — no frameworks, no magic. Built with a local Ollama model to understand exactly how tool calling works under the hood.

## What This Teaches

LLMs don't execute tools. They **decide** which tool to call and return structured JSON. Your code is responsible for:

1. Sending tool definitions (JSON schemas) alongside the prompt
2. Detecting when the LLM responds with a tool call instead of text
3. Executing the tool yourself
4. Feeding the result back to the LLM as a new message
5. Repeating until the LLM gives a final text answer

This project makes that entire loop visible in the UI — you can see tokens stream in, watch tool calls happen in real time, and trace the full request/response cycle.

## How Tool Calling Actually Works

### The old way (regex-based)

Before native tool calling support existed, people would:

1. Instruct the model (via system prompt) to output tool calls in a specific format, e.g. `<tool>{"name": "send_mail", "args": {...}}</tool>`
2. Parse the model's raw text output using regex to detect tool call patterns
3. Extract the function name and arguments from the matched text
4. Execute the tool and inject the result back into the conversation

This was fragile — models would sometimes output malformed JSON, forget the format, or mix tool call syntax with natural language. Every model needed different regex patterns.

### The modern way (native tool calling)

Ollama (and APIs like OpenAI, Anthropic, etc.) now have a **built-in tool calling pipeline**:

1. You send tool schemas (JSON) in the API request alongside the messages
2. Ollama injects a **model-specific system prompt template** that tells the model the expected tool call format (e.g., Hermes-style `<tool_call>{"name": "send_mail", ...}</tool_call>`)
3. The model generates tokens internally in that format
4. **Ollama's parser intercepts these tokens before they reach you** — it buffers them, parses the JSON, and sends you a clean `tool_calls` object in the response
5. You never see the raw tool call tokens — Ollama consumes them and gives you structured data

This is why in the UI you might see "(no text — model decided to call a tool directly)" — the model **did** generate tokens, but Ollama consumed them internally and returned the parsed result. The model's "reasoning" about which tool to call happens in the tokens that Ollama intercepts.

### Key takeaway

The LLM is just a text generator that was trained to output tool calls in a specific text format. The API layer (Ollama, OpenAI, etc.) handles the detection and parsing, so you get clean structured data instead of raw text you'd have to regex-match yourself.

## The Architecture

```
Browser (HTML/JS)
    │
    │  SSE stream
    ▼
FastAPI Backend
    │
    │  POST /api/chat (streaming)
    ▼
Ollama (qwen2.5:7b)
    │
    │  returns tool_calls
    ▼
Tool Registry (tools.py)
    │
    │  executes stub function (3-sec delay)
    ▼
Result fed back to Ollama → final response streamed to browser
```

## Tools (Stubs)

These are intentionally empty — the focus is the mechanism, not the integration.

| Tool | Description |
|---|---|
| `send_mail` | Send an email to a recipient |
| `schedule_meeting` | Schedule a meeting with attendees |
| `cancel_meeting` | Cancel a meeting by title and date |

Each tool has a 3-second delay so you can visually track the execution in the UI.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Ollama](https://ollama.com/) — local LLM runtime
- **qwen3:4b** model (~2.5 GB) — a thinking model with native tool calling support. We use a thinking model so you can see the model's internal reasoning (the `<think>` chain) before it decides which tool to call.

## Setup

Pull the model:

```bash
ollama pull qwen3:4b
```

That's it. `uv` handles the Python environment and dependencies automatically.

## Usage

```bash
# Start the server
./start.sh

# Open in browser
open http://localhost:8000

# Ctrl+C to stop
```

### Try these prompts

- "Send an email to john@example.com about tomorrow's standup"
- "Schedule a meeting with alice@co.com and bob@co.com for 2026-04-01 at 10:00 titled Sprint Planning"
- "Cancel the Sprint Planning meeting on 2026-04-01"

## Project Structure

```
├── main.py           # FastAPI backend — SSE streaming + tool call loop
├── tools.py          # Tool schemas (JSON) + stub implementations
├── static/
│   └── index.html    # Chat UI with streaming and tool call cards
├── start.sh          # Start the server (Ctrl+C to stop)
└── pyproject.toml    # Dependencies (managed by uv)
```
