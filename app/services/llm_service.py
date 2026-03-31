import logging

from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors

from app.config import settings

logger = logging.getLogger(__name__)

_genai_client: genai.Client | None = None


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        try:
            _genai_client = genai.Client(api_key=settings.google_api_key)
        except Exception as exc:
            logger.exception("Could not initialize Google GenAI client")
            raise HTTPException(status_code=500, detail="LLM client initialization failed") from exc
    return _genai_client


def build_prompt(question: str, context_chunks: list[str]) -> str:
    context = "\n\n".join(context_chunks)
    return (
        "You are a helpful assistant for professional SMEs such as law firms and accountants. "
        "Answer strictly using the provided context. If the context is insufficient, say it clearly.\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Answer:"
    )


async def generate_answer(question: str, context_chunks: list[str]) -> str:
    prompt = build_prompt(question=question, context_chunks=context_chunks)

    try:
        client = _get_genai_client()
        response = await client.aio.models.generate_content(model=settings.llm_model, contents=prompt)
    except genai_errors.ClientError as exc:
        message = str(exc)
        logger.exception("LLM API client error")
        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            # Extract retry delay from the error payload when available
            import re
            match = re.search(r"retryDelay.*?(\d+)s", message)
            retry_seconds = match.group(1) if match else "60"
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Gemini rate limit reached (free tier: 5 req/min for gemini-2.5-flash). "
                    f"Wait {retry_seconds}s and try again. "
                    "To remove this limit, enable billing at https://ai.dev/rate-limit"
                ),
            ) from exc
        if "401" in message or "403" in message or "PERMISSION_DENIED" in message:
            raise HTTPException(
                status_code=403,
                detail="Gemini authentication error. Verify GOOGLE_API_KEY.",
            ) from exc
        raise HTTPException(status_code=502, detail=f"LLM provider error: {message}") from exc
    except Exception as exc:
        logger.exception("LLM API request failed")
        raise HTTPException(status_code=502, detail="LLM API call failed. Check GOOGLE_API_KEY") from exc

    answer = response.text or ""

    clean_answer = answer.strip()
    if not clean_answer:
        raise HTTPException(status_code=502, detail="LLM returned an empty answer")

    return clean_answer
