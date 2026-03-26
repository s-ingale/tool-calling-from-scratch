# Tool Calling from Scratch

Implements LLM tool calling from scratch — no frameworks, no magic. Uses a local Ollama model to make the entire orchestration loop visible in the UI: thinking, tool calls, execution, and results.

## How Tool Calling Works

LLMs don't execute tools. They output structured text indicating which tool to call. Your code executes it and feeds the result back.

**Old way:** Prompt the model to output a specific format, regex-match it, parse manually. Fragile.

**Modern way (what we use):** Send tool schemas in the API request. Ollama intercepts the model's raw tool-call tokens, parses them, and returns clean structured `tool_calls` in the response. You never see the raw tokens — the API layer handles detection and parsing. Same approach as OpenAI, Anthropic, etc.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) with `qwen3:4b` (~2.5 GB, thinking model — so you can see the reasoning chain before tool calls)

```bash
ollama pull qwen3:4b
```

## Usage

```bash
./start.sh              # starts FastAPI on :8000
open http://localhost:8000
# Ctrl+C to stop
```

**Try:** "Send an email to john@example.com about tomorrow's standup" or "Schedule a meeting with alice@co.com on 2026-04-01 at 10:00"

## Architecture

```
Browser → SSE stream → FastAPI → Ollama (qwen3:4b)
                                    ↓ tool_calls
                              Tool Registry (tools.py)
                                    ↓ 3-sec stub execution
                              Result fed back to Ollama → streamed to browser
```

## Tools (Stubs)

| Tool | Params |
|---|---|
| `send_mail` | to, subject, body |
| `schedule_meeting` | title, attendees[], date, time |
| `cancel_meeting` | title, date |

3-second delay per tool so you can watch execution in the UI.

## Project Structure

```
main.py             # FastAPI backend — SSE streaming + tool call loop
tools.py            # Tool schemas (JSON) + stub implementations (3-sec delay)
static/index.html   # Chat UI with orchestration pipeline
static/styles.css   # Styles
start.sh            # Start script (checks Ollama, runs uvicorn)
```
