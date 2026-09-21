import base64
import os
import time
from pathlib import Path

from openai import OpenAI


MODEL = "qwen/qwen3.8-27b"
BASE_URL = "https://api.groq.com/openai/v1"

MAX_TOKENS = 1000
TEMPERATURE = 0.7
REASONING_EFFORT = "none"

# Conservative local guard. This is deliberately below the documented
# daily limit so the runner does not consume the entire daily budget.
DAILY_TOKEN_GUARD = 180_000

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 5


client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=BASE_URL,
)


def encode_image(path: Path) -> str:
    with path.open("rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


def extract_usage(response) -> dict:
    usage = response.usage

    if usage is None:
        return {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }

    return {
        "prompt_tokens": getattr(
            usage,
            "prompt_tokens",
            None,
        ),
        "completion_tokens": getattr(
            usage,
            "completion_tokens",
            None,
        ),
        "total_tokens": getattr(
            usage,
            "total_tokens",
            None,
        ),
    }


def query(
    messages: list,
    *,
    token_budget_used: int,
) -> tuple[str, dict]:

    if token_budget_used >= DAILY_TOKEN_GUARD:
        raise RuntimeError(
            "Local daily token guard reached: "
            f"{token_budget_used} >= {DAILY_TOKEN_GUARD}"
        )

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        start = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                reasoning_effort=REASONING_EFFORT,
            )

            elapsed = time.perf_counter() - start

            output = response.choices[0].message.content

            if output is None:
                raise RuntimeError(
                    "VLM returned no message content."
                )

            usage = extract_usage(response)

            total_tokens = usage["total_tokens"]

            if total_tokens is not None:
                if (
                    token_budget_used + total_tokens
                    > DAILY_TOKEN_GUARD
                ):
                    raise RuntimeError(
                        "This response would exceed the local "
                        f"daily token guard: "
                        f"{token_budget_used} + "
                        f"{total_tokens} > "
                        f"{DAILY_TOKEN_GUARD}"
                    )

            record = {
                "api_attempt": attempt,
                "latency_seconds": elapsed,
                **usage,
                "finish_reason": (
                    response.choices[0].finish_reason
                ),
            }

            return output, record

        except Exception as exc:
            last_error = exc

            status_code = getattr(
                exc,
                "status_code",
                None,
            )

            if status_code != 429:
                raise

            if attempt >= MAX_RETRIES:
                raise

            sleep_seconds = (
                INITIAL_BACKOFF_SECONDS
                * (2 ** (attempt - 1))
            )

            time.sleep(sleep_seconds)

    raise RuntimeError(
        f"API request failed after retries: {last_error}"
    )
def query_initial(
    *,
    image_path: Path,
    prompt: str,
    token_budget_used: int,
) -> tuple[str, dict]:
    """Run the unchanged Phase 3 generation as Phase 4 attempt 1.

    This deliberately uses the Phase 3 generation settings:
    temperature=0, max_tokens=1000, reasoning_effort=none.
    """
    image_b64 = encode_image(image_path)

    if token_budget_used >= DAILY_TOKEN_GUARD:
        raise RuntimeError(
            "Local daily token guard reached: "
            f"{token_budget_used} >= {DAILY_TOKEN_GUARD}"
        )

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        start = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        "data:image/png;base64,"
                                        + image_b64
                                    )
                                },
                            },
                        ],
                    }
                ],
                temperature=0,
                max_tokens=1000,
                reasoning_effort="none",
            )

            elapsed = time.perf_counter() - start

            output = response.choices[0].message.content

            if output is None:
                raise RuntimeError(
                    "VLM returned no message content."
                )

            usage = extract_usage(response)
            total_tokens = usage["total_tokens"]

            if total_tokens is not None:
                if token_budget_used + total_tokens > DAILY_TOKEN_GUARD:
                    raise RuntimeError(
                        "This response would exceed the local "
                        f"daily token guard: "
                        f"{token_budget_used} + "
                        f"{total_tokens} > "
                        f"{DAILY_TOKEN_GUARD}"
                    )

            record = {
                "api_attempt": attempt,
                "latency_seconds": elapsed,
                **usage,
                "finish_reason": response.choices[0].finish_reason,
            }

            return output, record

        except Exception as exc:
            last_error = exc
            status_code = getattr(exc, "status_code", None)

            if status_code != 429:
                raise

            if attempt >= MAX_RETRIES:
                raise

            sleep_seconds = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
            time.sleep(sleep_seconds)

    raise RuntimeError(
        f"Initial VLM request failed after retries: {last_error}"
    )
