from typing import Any
import asyncio
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime
from langgraph_email.schemas.extract_intent_details import extract_intent_details
from langgraph_email.workflow.context import EmailContext
from langgraph_email.workflow.state import EmailState
from pydantic import EmailStr, TypeAdapter, ValidationError
from langgraph_email.extractor import extract_email_request
from langgraph_email.mcp_client import create_mcp_client
from langgraph.types import interrupt
from html import escape
from uuid import uuid4


You are an expert AI Email Processing Assistant. Your sole task is to analyze incoming user requests regarding emails, extract structured details, and determine the exact action to perform.

### Extracted Fields
1. **intent**: Determine the target action. Must strictly be one of the following two values:
   - "send-email": Select this when the user explicitly instructs to send, deliver, or dispatch an email immediately.
   - "save-draft": Select this when the user explicitly asks to draft, save, compose for later, or when the request phrasing implies an unfinished/review-first draft (e.g., "prepare an email", "write a draft", "save this").

2. **to**: Extract the target recipient's email address.
   - If a full email address is provided (e.g., `za@gmail.com`), extract it directly.
   - If only a name is given and no email address is present, set this to an empty string (`""`).

3. **subject**: Construct or extract an appropriate, concise email subject line.
   - If explicitly stated in the input, extract it directly.
   - If not stated, infer a clear, concise professional subject line (3 to 7 words) summarizing the core topic.

4. **body**: Extract or generate the main message content.
   - If the user provides explicit message text, capture or format it cleanly.
   - If the user provides only high-level instructions (e.g., "tell him the meeting is moved"), expand it into a complete, professional, and context-appropriate email body.

### Rules & Formatting
- Never include fields outside the required schema.
- Maintain a polite, professional tone in generated email bodies unless the original text specifies a distinct tone.


async def input_node(state: EmailState) -> dict[str, Any]:
    user_prompt = str(input("You: ")).strip()

    return {
        "messages": [HumanMessage(content=user_prompt)],
        "user_prompt": user_prompt,
        "user_intent": "unknown",
        "model_response": {},
    }



async def analyze_intent_extract_content(
    state: EmailState,
    runtime: Runtime[EmailContext],
) -> dict[str, Any]:

    response = await runtime.context.model.with_structured_output(extract_intent_details).invoke(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": state["user_prompt"]},
        ]
    )

    


async def extract_details(
    state: EmailState,
    runtime: Runtime[EmailContext],
) -> dict[str, Any]:
    request = await extract_email_request(
        user_prompt=state["user_prompt"],
        model=runtime.context.model,
    )

    details = {
        "to": request.to,
        "subject": (request.subject or "").strip(),
        "body_text": (request.body_text or "").strip(),
    }

    errors = []

    if len(details["to"]) > 100:
        errors.append("Use no more than 100 recipients.")
    elif details["to"]:
        try:
            details["to"] = recipient_validator.validate_python(
                details["to"]
            )
        except ValidationError:
            errors.append("Provide valid recipient email addresses.")

    if len(details["subject"]) > 998:
        errors.append("Keep the subject within 998 characters.")

    if len(details["body_text"]) > 1_000_000:
        errors.append("Keep the message within 1,000,000 characters.")

    details["validation_errors"] = errors

    return details


async def prepare_draft_node(
    state: EmailState,
    runtime: Runtime[EmailContext],
) -> dict[str, Any]:
    details = await extract_details(state, runtime)

    has_content = bool(
        details["to"]
        or details["subject"]
        or details["body_text"]
    )

    if details["validation_errors"]:
        message = " ".join(details["validation_errors"])
    elif not has_content:
        message = (
            "Please provide at least one recipient email address, a subject, or message content for the draft."
        )
    else:
        message = "Draft details are ready."
        details["create_draft_key"] = str(uuid4())

    details["message"] = message

    return {"model_response": details}

async def save_draft_node(
    state: EmailState,
    runtime: Runtime[EmailContext],
) -> dict[str, Any]:
    details = state["model_response"]
    settings = runtime.context.settings

    operation_key = details.get("create_draft_key")

    if not operation_key:
        raise ValueError("The draft operation key is missing.")

    payload = {
        "type": "new",
        "to": details["to"],
    }

    if details["subject"]:
        payload["subject"] = details["subject"]

    if details["body_text"]:
        text = details["body_text"]
        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
        html_body = escape(normalized_text).replace("\n", "<br>")

        payload["bodyText"] = text
        payload["bodyHtml"] = f"<p>{html_body}</p>"

    async with create_mcp_client(settings) as client:
        result = await client.call_tool(
            "create_draft",
            {
                "mailbox_id": str(settings.vyzno_mailbox_id),
                "draft": payload,
                "idempotency_key": operation_key,
            },
            timeout=60.0,
        )

    data = result.structured_content

    if (
        not isinstance(data, dict)
        or not data.get("id")
        or data.get("status") != "draft"
    ):
        raise RuntimeError(
            "Draft creation was not confirmed. "
            "Check Vyzno before retrying."
        )

    return {
        "model_response": {
            **details,
            "draft_id": data["id"],
            "status": data["status"],
            "message": f"Draft saved. Draft ID: {data['id']}",
        },
    }


async def prepare_email_node(
    state: EmailState,
    runtime: Runtime[EmailContext],
) -> dict[str, Any]:
    details = await _extract_details(state, runtime)

    missing_fields = []

    if not details["to"]:
        missing_fields.append("recipient email address")

    if not details["subject"]:
        missing_fields.append("subject")

    if not details["body_text"]:
        missing_fields.append("message content")

    if details["validation_errors"]:
        message = " ".join(details["validation_errors"])
    elif missing_fields:
        message = "Please provide: " + ", ".join(missing_fields) + "."
    else:
        message = "Email details are ready."
        details["create_draft_key"] = str(uuid4())
        details["send_draft_key"] = str(uuid4())

    details["missing_fields"] = missing_fields
    details["message"] = message

    return {"model_response": details}

async def send_email_node(
    state: EmailState,
    runtime: Runtime[EmailContext],
) -> dict[str, Any]:
    send_key = state["model_response"].get("send_draft_key")

    if not send_key:
        raise ValueError("The send operation key is missing.")

    draft_update = await save_draft_node(state, runtime)
    details = draft_update["model_response"]

    settings = runtime.context.settings

    async with create_mcp_client(settings) as client:
        result = await client.call_tool(
            "send_draft",
            {
                "mailbox_id": str(settings.vyzno_mailbox_id),
                "draft_id": details["draft_id"],
                "idempotency_key": send_key,
            },
            timeout=120.0,
        )

    data = result.structured_content

    if (
        not isinstance(data, dict)
        or data.get("id") != details["draft_id"]
        or data.get("status") != "sent"
    ):
        raise RuntimeError(
            "Sending was not confirmed. "
            "Check the message status in Vyzno before retrying."
        )

    return {
        "model_response": {
            **details,
            "status": data["status"],
            "message": f"Email sent. Message ID: {data['id']}",
        },
    }