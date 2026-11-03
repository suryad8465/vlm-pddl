"""Dataset generation entry point.

Iterates over all combinations of 3 layouts × 3 task types × 3 instruction
styles (27 total) and calls ``create_scenario`` for each, producing a
sequentially numbered ``scenario_NNN/`` directory tree under ``scenarios/``.

Run directly as a script to (re-)generate the full dataset.
"""

from sim.scenario import create_scenario
from sim.state import (
    baseline_state,
    layout_2_state,
    layout_3_state,
)


LAYOUTS = {
    "baseline": baseline_state,
    "layout_2": layout_2_state,
    "layout_3": layout_3_state,
}

TASK_TYPES = (
    "navigation",
    "retrieval",
    "multi_step",
)

INSTRUCTION_STYLES = (
    "precise",
    "ambiguous",
    "novel",
)


def scenario_id(number: int) -> str:
    """Return a zero-padded scenario identifier string.

    Args:
        number: Sequential scenario number starting from 1.

    Returns:
        A string like "scenario_003".
    """
    return f"scenario_{number:03d}"


def main() -> None:
    """Generate the full dataset of 27 scenarios.

    Iterates over all 3 layouts × 3 task types × 3 instruction styles,
    assigning default goal configurations and calling create_scenario for each.
    """
    number = 1

    for layout_name, state_factory in LAYOUTS.items():
        state = state_factory()

        for task_type in TASK_TYPES:
            for instruction_style in INSTRUCTION_STYLES:
                if task_type == "navigation":
                    goal_object = None
                    goal_location = "kitchen"
                else:
                    goal_object = "mug"
                    goal_location = "living_room"

                create_scenario(
                    scenario_id=scenario_id(number),
                    state=state,
                    goal_object=goal_object,
                    goal_location=goal_location,
                    layout=layout_name,
                    task_type=task_type,
                    instruction_style=instruction_style,
                )

                number += 1


if __name__ == "__main__":
    main()
