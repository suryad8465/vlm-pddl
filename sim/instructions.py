"""Natural-language task instruction generator.

Generates fixed instruction strings for the three task types
(navigation, retrieval, multi_step) crossed with three instruction styles
(precise, ambiguous, novel). Used during dataset generation to populate each
scenario's ``instruction.txt``.
"""

from typing import Literal


# Permitted task categories for this dataset.
TaskType = Literal[
    "navigation",
    "retrieval",
    "multi_step",
]

# Permitted instruction phrasings:
#   precise   – unambiguous destination and object.
#   ambiguous – destination is underspecified ("over there").
#   novel     – paraphrased using informal synonyms (e.g. "lounge").
InstructionStyle = Literal[
    "precise",
    "ambiguous",
    "novel",
]


def make_instruction(
    task_type: TaskType,
    style: InstructionStyle,
    object_name: str = "mug",
    destination: str = "living_room",
) -> str:
    """Return a hard-coded natural-language instruction string.

    Instruction text is fixed per (task_type, style) pair; object_name and
    destination are interpolated where the phrasing allows.

    Args:
        task_type: One of "navigation", "retrieval", or "multi_step".
        style: One of "precise", "ambiguous", or "novel".
        object_name: Name of the object to retrieve (used for retrieval and
            multi_step tasks).
        destination: Target location name (used for precise retrieval only).

    Returns:
        A natural-language instruction string.

    Raises:
        ValueError: If task_type or style is not a recognised value.
    """
    if task_type not in {
        "navigation",
        "retrieval",
        "multi_step",
    }:
        raise ValueError(f"Unknown task type: {task_type}")

    if style not in {
        "precise",
        "ambiguous",
        "novel",
    }:
        raise ValueError(f"Unknown instruction style: {style}")

    if task_type == "navigation":
        if style == "precise":
            return "Go to the kitchen."

        if style == "ambiguous":
            return "Go over there."

        return "Head into the cooking area."

    if task_type == "retrieval":
        if style == "precise":
            return f"Bring the {object_name} to the living room."

        if style == "ambiguous":
            return f"Bring the {object_name} over there."

        return "Take the cup into the lounge."

    if style == "precise":
        return (
            f"Go to the kitchen, pick up the {object_name}, "
            "and take it to the living room."
        )

    if style == "ambiguous":
        return (
            f"Go get the {object_name} "
            "and bring it over there."
        )

    return (
        "Head to the cooking area, collect the cup, "
        "and carry it into the lounge."
    )
