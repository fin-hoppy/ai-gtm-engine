
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from moss import inference


async def _generate(prompt: str) -> str:
    if not os.getenv("MOSS_PROJECT_ID"):
        raise RuntimeError("MOSS_PROJECT_ID is missing.")

    if not os.getenv("MOSS_PROJECT_KEY"):
        raise RuntimeError("MOSS_PROJECT_KEY is missing.")

    response = await inference.responses.create(
        model="moss",
        input=prompt,
    )

    return response.output_text


def generate(prompt: str) -> str:
    return asyncio.run(_generate(prompt))
