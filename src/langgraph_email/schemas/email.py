from pydantic import BaseModel, ConfigDict, Field

class EmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to: list[str] = Field(
        description=(
            "Recipient email addresses explicitly provided by the user. "
            "Never guess an address from a person's name. "
            "Return an empty list when no address is available."
        ),
    )

    subject: str | None = Field(
        description=(
            "The requested subject, or a concise subject derived "
            "from the requested message. "
            "Return null when there is insufficient information."
        ),
    )

    body_text: str | None = Field(
        description=(
            "The plain-text email message based on the user's instructions. "
            "Preserve their meaning and do not invent facts. "
            "Return null when the message content is missing."
        ),
    )