import base64
from pathlib import Path

from pipeline.phase4.api import query


def build_verifier_messages(
    *,
    image_path: Path,
    instruction: str,
    pddl_text: str,
) -> list:
    """Build the Phase 4 B self-verification request.

    Ground truth is deliberately excluded.
    """

    with image_path.open("rb") as image_file:
        image_b64 = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    system_prompt = """You are a verifier for a vision-language-to-PDDL
household planning system.

Inspect the supplied scene image and the original instruction. Then inspect
the generated PDDL problem.

Determine whether the generated PDDL is CONSISTENT with the information
supported by the image and instruction.

Do not use ground truth.
Do not invent facts that are not visually or linguistically supported.

Return exactly one of:

CONSISTENT

or:

INCONSISTENT
REASON: <one concise, specific discrepancy>

If the available evidence is insufficient to establish a discrepancy,
return CONSISTENT.

Do not return explanations outside the required format.
Do not return markdown fences.
"""

    user_text = f"""Original instruction:
{instruction}

Generated PDDL:
{pddl_text}

Verify the generated PDDL against the image and instruction.
"""

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_text,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                    },
                },
            ],
        },
    ]


def parse_verifier_response(text: str) -> dict:
    """Parse B's constrained response format."""

    cleaned = text.strip()

    if cleaned == "CONSISTENT":
        return {
            "status": "CONSISTENT",
            "reason": None,
        }

    prefix = "INCONSISTENT"
    if cleaned.startswith(prefix):
        remainder = cleaned[len(prefix):].strip()

        if remainder.startswith("REASON:"):
            reason = remainder[len("REASON:"):].strip()
        else:
            reason = remainder or None

        return {
            "status": "INCONSISTENT",
            "reason": reason,
        }

    return {
        "status": "INVALID",
        "reason": "Verifier returned an unrecognized response.",
    }


def query_verifier(
    *,
    image_path: Path,
    instruction: str,
    pddl_text: str,
    token_budget_used: int,
) -> tuple[dict, dict]:
    """Run B self-verification using the Phase 4 refinement API settings."""

    messages = build_verifier_messages(
        image_path=image_path,
        instruction=instruction,
        pddl_text=pddl_text,
    )

    raw_response, api_record = query(
        messages,
        token_budget_used=token_budget_used,
    )

    result = parse_verifier_response(raw_response)

    return result, {
        "raw_response": raw_response,
        **api_record,
    }
