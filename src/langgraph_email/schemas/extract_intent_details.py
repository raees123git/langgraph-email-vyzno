from typing import Literal
from pydantic import BaseModel, Field


class EmailAnalysis(BaseModel):
  intent: Literal["send-email", "save-draft"] = Field(
      description=(
          "The classified intent of the request. Must be either 'send-email' or"
          " 'save-draft'."
      )
  )
  to: str = Field(
      description="The recipient email address extracted from the text."
  )
  subject: str = Field(
      description="The subject line for the email.", default=""
  )
  body: str = Field(
      description="The full content/body of the email message.", default=""
  )