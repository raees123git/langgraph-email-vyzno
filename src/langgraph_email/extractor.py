from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_email.schemas.email import EmailRequest

SYSTEM_PROMPT = """
Extract email details from the user's request.

Rules:
- Include only recipient email addresses explicitly provided.
  Never invent an address from a person's name.
- Preserve an explicitly provided subject.
  Otherwise, derive a concise subject from the message
  when there is sufficient information.
- Write the plain-text message from the user's instructions.
  Preserve their meaning and do not invent facts.
- Return an empty recipient list when addresses are missing.
- Return null for a subject or body that cannot be determined.
- Read follow-up replies together with the original request.
- Preserve earlier details unless the user changes them.
- Apply the user's latest corrections.
- Return the requested structure without claiming an action has been performed.
"""


async def extract_email_request(
    user_prompt: str,
    model: ChatGoogleGenerativeAI,
    conversation: list[dict[str, str]] | None = None,
) -> EmailRequest:
    if not user_prompt.strip():
        raise ValueError("The user prompt cannot be empty.")

    structured_model = model.with_structured_output(
        EmailRequest,
        method="json_schema",
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    if conversation:
        messages.extend(conversation)
    else:
        messages.append(
            {"role": "user", "content": user_prompt}
        )

    result = await structured_model.ainvoke(messages)

    return EmailRequest.model_validate(result)