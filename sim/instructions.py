from typing import Literal


TaskType = Literal[
    "navigation",
    "retrieval",
    "multi_step",
]

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
