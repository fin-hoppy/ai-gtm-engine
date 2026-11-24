
import asyncio
import os

from dotenv import load_dotenv
from moss import inference

load_dotenv()


async def main():
    if not os.getenv("MOSS_PROJECT_ID"):
        raise RuntimeError("MOSS_PROJECT_ID is missing.")

    if not os.getenv("MOSS_PROJECT_KEY"):
        raise RuntimeError("MOSS_PROJECT_KEY is missing.")

    response = await inference.responses.create(
        model="moss",
        input="Reply only with: MOSS API connection successful."
    )

    print(response.output_text)


if __name__ == "__main__":
    asyncio.run(main())
