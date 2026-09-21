import base64
from pathlib import Path


def build_refinement_messages(
    *,
    image_path: Path,
    instruction: str,
    previous_pddl: str,
    feedback: str,
) -> list:
    """Build a Phase 4 refinement request.

    The model receives the scene image, original instruction, its previous
    PDDL candidate, and deployment-time feedback. Ground truth is never
    included.
    """
    with image_path.open("rb") as image_file:
        image_b64 = base64.b64encode(image_file.read()).decode("utf-8")

    system_prompt = """You are a vision-language planning system.

Generate a PDDL problem for the household planning domain from the scene
image and natural-language instruction.

You are refining a previous PDDL candidate using deployment-time feedback
from the planning pipeline. Correct the candidate when the feedback provides
evidence that it is invalid or cannot be deployed.

Do not use ground truth or assume facts that are not supported by the image
or instruction.

If the available evidence is insufficient to determine a required fact,
request clarification rather than inventing the fact.

Return exactly one of:

STATUS: PDDL
<PDDL problem>

or:

STATUS: CLARIFICATION_REQUIRED
REASON: <brief reason>

Do not include markdown fences or explanations outside this format.
"""

    user_text = f"""Original instruction:
{instruction}

Previous PDDL candidate:
{previous_pddl}

Deployment-time feedback:
{feedback}

Produce the corrected candidate now.
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
