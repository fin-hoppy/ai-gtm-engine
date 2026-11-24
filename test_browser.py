import asyncio
import os

from dotenv import load_dotenv
from moss import MossInference

load_dotenv()


async def main():
    async with MossInference(
        os.environ["MOSS_PROJECT_ID"],
        os.environ["MOSS_PROJECT_KEY"],
    ) as client:

        task = await client.tasks.run(
            goal=(
                "Visit https://example.com and "
                "return the page title."
            ),
            environment={
                "type": "browser",
                "start_url": "https://example.com",
            },
            output_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"}
                },
                "required": ["title"],
            },
            limits={
                "max_runtime_seconds": 60,
                "max_cost_usd": 0.50,
            },
            timeout=90,
        )

        print("Task ID:", getattr(task, "id", None))
        print("Status:", task.status)
        print("Error:", getattr(task, "error", None))
        print("Result:", getattr(task, "result", None))
        print("Usage:", getattr(task, "usage", None))


if __name__ == "__main__":
    asyncio.run(main())