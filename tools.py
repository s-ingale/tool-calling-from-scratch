import asyncio
import json

# --- Tool Definitions (JSON schemas sent to the LLM) ---

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "send_mail",
            "description": "Send an email to a recipient with a subject and body",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedule a meeting with attendees at a specific date and time",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Meeting title",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                    "date": {
                        "type": "string",
                        "description": "Meeting date in YYYY-MM-DD format",
                    },
                    "time": {
                        "type": "string",
                        "description": "Meeting time in HH:MM format (24-hour)",
                    },
                },
                "required": ["title", "attendees", "date", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_meeting",
            "description": "Cancel a previously scheduled meeting by its title and date",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the meeting to cancel",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date of the meeting in YYYY-MM-DD format",
                    },
                },
                "required": ["title", "date"],
            },
        },
    },
]


# --- Tool Implementations (stubs with 3-sec delay) ---


async def send_mail(to: str, subject: str, body: str) -> str:
    await asyncio.sleep(3)
    return json.dumps({
        "status": "sent",
        "message": f"Email sent to {to} with subject '{subject}'",
    })


async def schedule_meeting(
    title: str, attendees: list[str], date: str, time: str
) -> str:
    await asyncio.sleep(3)
    return json.dumps({
        "status": "scheduled",
        "message": f"Meeting '{title}' scheduled on {date} at {time} with {', '.join(attendees)}",
    })


async def cancel_meeting(title: str, date: str) -> str:
    await asyncio.sleep(3)
    return json.dumps({
        "status": "cancelled",
        "message": f"Meeting '{title}' on {date} has been cancelled",
    })


# --- Tool Registry (maps name -> function) ---

TOOL_REGISTRY: dict[str, callable] = {
    "send_mail": send_mail,
    "schedule_meeting": schedule_meeting,
    "cancel_meeting": cancel_meeting,
}


async def execute_tool(name: str, arguments: dict) -> str:
    """Look up a tool by name and execute it with the given arguments."""
    tool_fn = TOOL_REGISTRY.get(name)
    if not tool_fn:
        return json.dumps({"status": "error", "message": f"Unknown tool: {name}"})
    return await tool_fn(**arguments)
