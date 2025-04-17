import asyncio
import logging
import os
import re

import httpx
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

logger = logging.getLogger(__name__)


async def web_scrape_job_description(url: str) -> dict[str, str]:
    """
    Web scrape the given job listing url and return the job description.
    Currently supports listings from linkedIn and myworkdayjobs.
    Returns a dict with status: success or error and message: job description or error message
    """
    is_valid, message = _validate_url(url)
    if not is_valid:
        return {"status": "error", "message": message}
    try:
        async with httpx.AsyncClient() as client:
            JINA_API_KEY = os.getenv("JINA_API_KEY")
            headers = (
                {
                    "Authorization": f"Bearer {JINA_API_KEY}",
                }
                if JINA_API_KEY
                else {}
            )
            response = await client.get(
                _use_jina(url),
                timeout=20,
                headers=headers,
            )
            logger.info(f"Scraped {url} successfully using jina")
            return {
                "status": "success",
                "message": await _extract_job_description(response.text[: 4000 * 4]),
            }
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return {"status": "error", "message": str(e)}


def _validate_url(url: str) -> tuple[bool, str]:
    """Validate the given url.
    Returns True if the url is jina parseable. Currently supports linkedin and myworkdayjobs.
    """

    if not url.startswith("https://"):
        logger.error(f"Invalid URL: {url} does not start with https://")
        return (False, "Invalid URL, must start with https://")

    patterns = [
        r"https://www\.linkedin\.com/jobs/view/[a-zA-Z0-9_-]+",
        r"https://\w+\.wd\d\.myworkdayjobs\.com/.+?/job/.+",
    ]
    if not any(re.match(pattern, url) for pattern in patterns):
        logger.error(
            f"Unsupported URL: {url} is not supported, please use a linkedin or myworkdayjobs url"
        )
        return (False, "Unsupported URL, must be a linkedin or myworkdayjobs url")
    return (True, "Valid URL")


async def _extract_job_description(text: str) -> str:
    """Extract the relevant job description from the given markdown text."""
    llm = init_chat_model(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_provider="openai",
        model="gpt-4o-mini",
    )
    system_instructions = """
    Extract the relevant job description from the given markdown text.
    Only return the job description, do not include any other text.
    """
    messages = [
        SystemMessage(content=system_instructions),
        HumanMessage(content=text),
    ]
    response = await llm.ainvoke(messages)
    logger.info(f"Extracted job description: {len(response.content)} characters")
    logger.debug(f"Extracted job description: content={response.content}")
    return response.content


def _use_jina(url: str) -> str:
    """prefix the url with jina.ai"""
    return f"https://r.jina.ai/{url}"


async def main(url: str):
    print(await web_scrape_job_description(url))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(input("Enter the url: ")))
