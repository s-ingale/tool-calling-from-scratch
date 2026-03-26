import json

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from tools import TOOL_SCHEMAS, execute_tool

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "qwen3:4b"
SYSTEM_PROMPT = (
    "You are a helpful personal assistant. "
    "You can send emails, schedule meetings, and cancel meetings. "
    "Use the provided tools when the user asks you to perform these actions. "
    "Always confirm what you did after using a tool."
)


class ChatRequest(BaseModel):
    messages: list[dict]


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": MODEL}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    SSE endpoint that streams the LLM response.

    Event types sent to the frontend:
      - "token"        : a chunk of assistant text
      - "tool_call"    : the LLM wants to call a tool (name + args)
      - "tool_running" : tool execution has started
      - "tool_result"  : tool execution finished (with result)
      - "done"         : stream is complete
      - "error"        : something went wrong
    """

    # Prepend system prompt to conversation
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + request.messages

    async def event_stream():
        try:
            async for event in _run_chat_loop(messages):
                yield event
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


async def _run_chat_loop(messages: list[dict]):
    """
    Core loop: send messages to Ollama, stream tokens, handle tool calls,
    feed results back, and repeat until the model gives a final text answer.
    """
    while True:
        # Collect the full assistant response while streaming tokens
        assistant_content = ""
        tool_calls = []

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    "tools": TOOL_SCHEMAS,
                    "stream": True,
                    "think": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    chunk = json.loads(line)
                    msg = chunk.get("message", {})
                    # Debug: log raw chunks to terminal
                    if msg.get("tool_calls") or msg.get("thinking") or chunk.get("done"):
                        print(f"[DEBUG] chunk: {json.dumps(chunk)[:300]}")

                    # Stream thinking tokens (reasoning chain)
                    thinking = msg.get("thinking", "")
                    if thinking:
                        yield {
                            "event": "thinking",
                            "data": json.dumps({"content": thinking}),
                        }

                    # Stream text tokens to the frontend
                    content = msg.get("content", "")
                    if content:
                        assistant_content += content
                        yield {
                            "event": "token",
                            "data": json.dumps({"content": content}),
                        }

                    # Collect tool calls (arrive as a single chunk)
                    if msg.get("tool_calls"):
                        tool_calls.extend(msg["tool_calls"])

        # If no tool calls, we're done — the model gave a final answer
        if not tool_calls:
            yield {"event": "done", "data": json.dumps({"finished": True})}
            return

        # --- Tool call handling ---

        # Append the assistant's message (with tool_calls) to history
        messages.append({
            "role": "assistant",
            "content": assistant_content,
            "tool_calls": tool_calls,
        })

        # Execute each tool call and feed results back
        for tc in tool_calls:
            func = tc["function"]
            tool_name = func["name"]
            tool_args = func["arguments"]

            # Tell the frontend which tool is being called
            yield {
                "event": "tool_call",
                "data": json.dumps({"name": tool_name, "arguments": tool_args}),
            }

            # Tell the frontend tool is now running
            yield {
                "event": "tool_running",
                "data": json.dumps({"name": tool_name}),
            }

            # Execute the tool (3-sec delay built in)
            result = await execute_tool(tool_name, tool_args)

            # Tell the frontend the result
            yield {
                "event": "tool_result",
                "data": json.dumps({"name": tool_name, "result": json.loads(result)}),
            }

            # Append tool result to conversation history for the LLM
            messages.append({
                "role": "tool",
                "content": result,
                "tool_name": tool_name,
            })

        # Signal the frontend that all tool results are in
        # and the LLM is about to process them
        yield {
            "event": "tool_result_done",
            "data": json.dumps({"message": "All tool results collected, sending back to LLM"}),
        }

        # Clear tool_calls and loop back — the LLM will now see the tool
        # results and either call more tools or give a final answer
        tool_calls = []
