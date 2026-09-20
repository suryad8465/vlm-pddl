from pathlib import Path
import json

from sim.instructions import make_instruction
from sim.io import save_state
from sim.pddl import save_ground_truth_problem
from sim.render_scene import render_scene
from sim.state import SceneState


def create_scenario(
    scenario_id: str,
    state: SceneState,
    goal_location: str,
    goal_object: str | None = None,
    layout: str = "baseline",
    task_type: str = "retrieval",
    instruction_style: str = "precise",
    output_root: str | Path = "scenarios",
) -> Path:
    """Generate all artifacts for one scenario."""
    if task_type not in {"navigation", "retrieval", "multi_step"}:
        raise ValueError(f"Unknown task type: {task_type}")

    if task_type == "navigation":
        goal_type = "navigation"
        goal_object = None
    else:
        goal_type = "retrieval"

        if goal_object is None:
            raise ValueError(
                f"{task_type} tasks require goal_object"
            )
    instruction = make_instruction(
        task_type=task_type,
        style=instruction_style,
        object_name=goal_object or "mug",
        destination=goal_location,
    )
    scenario_dir = Path(output_root) / scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)

    # Canonical state
    save_state(
        state,
        scenario_dir / "state.json",
    )

    # Ground-truth PDDL
    save_ground_truth_problem(
        state=state,
        path=scenario_dir / "gt_problem.pddl",
        goal_object=goal_object,
        goal_location=goal_location,
        goal_type=goal_type,
        problem_name=scenario_id,
    )
    # Scene image
    render_scene(
        state,
        scenario_dir / "scene.png",
    )

    # Natural-language instruction
    (scenario_dir / "instruction.txt").write_text(
        instruction.strip() + "\n"
    )

    # Scenario metadata
    metadata = {
        "scenario_id": scenario_id,
        "layout": layout,
        "task_type": task_type,
        "instruction_style": instruction_style,
        "goal": {
            "type":goal_type,
            "object": goal_object,
            "location": goal_location,
        },
        "files": {
            "scene": "scene.png",
            "state": "state.json",
            "ground_truth_problem": "gt_problem.pddl",
            "instruction": "instruction.txt",
        },
    }

    (scenario_dir / "scenario.json").write_text(
        json.dumps(metadata, indent=2) + "\n"
    )

    return scenario_dir
