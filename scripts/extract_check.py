import argparse
import asyncio

from langgraph_email.config import Settings
from langgraph_email.extractor import extract_email_request
from langgraph_email.model import create_model


async def main(user_prompt: str) -> None:
    settings = Settings()
    model = create_model(settings)

    result = await extract_email_request(user_prompt, model)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract email details from a user prompt."
    )
    parser.add_argument("prompt")
    arguments = parser.parse_args()

    asyncio.run(main(arguments.prompt))