# Tool Calling from Scratch

Implements LLM tool calling **truly from scratch** — no native tool calling APIs, no frameworks. We inject tool definitions into the system prompt, the model outputs `<tool_call>` XML tags as raw text, and we parse them ourselves in real-time as tokens stream in.

## How It Works

1. **System prompt** tells the model what tools exist and to use `<tool_call>{"name": "...", "arguments": {...}}</tool_call>` format
2. Model generates tokens — our **stream parser** watches for `<tool_call>` tags incrementally as tokens arrive one at a time
3. Once `</tool_call>` is detected, we **parse the JSON** and execute the tool
4. Tool result is injected back into the conversation as a `<tool_response>` message
5. Loop back to the model until it gives a final text answer

The UI makes every step visible: thinking chain, raw model output (watch it write the JSON character by character), parsed tool call, execution with timer, and the full context sent to the LLM at each round (click "View LLM Input").

### Why not use Ollama's native tool calling?

Ollama (and OpenAI, Anthropic, etc.) have built-in tool calling that intercepts the model's raw tokens, parses them, and returns clean structured data. We deliberately skip that to understand the layer underneath — the same layer those APIs implement internally.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) with `qwen3:4b` (~2.5 GB, thinking model)

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
Browser → SSE stream → FastAPI → Stream Parser → Ollama (qwen3:4b)
                                      ↓
                          detects <tool_call> tags in raw token stream
                                      ↓
                          parses JSON, executes tool (3-sec stub)
                                      ↓
                          injects <tool_response> into conversation
                                      ↓
                          loops back to Ollama → streams to browser
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
main.py             # FastAPI backend — SSE streaming + tool call orchestration
parser.py           # Real-time stream parser — detects <tool_call> tags incrementally
tools.py            # Tool schemas, system prompt builder, stub implementations
static/index.html   # Chat UI with orchestration pipeline
static/styles.css   # Styles
start.sh            # Start script (checks Ollama, runs uvicorn)
```
