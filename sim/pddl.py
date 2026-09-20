from pathlib import Path

from sim.state import SceneState


DOMAIN_NAME = "household"


def ground_truth_problem(
    state: SceneState,
    goal_location: str,
    goal_object: str | None = None,
    goal_type: str = "retrieval",
    problem_name: str = "ground_truth",
) -> str:
    object_names = [obj.name for obj in state.objects]

    if goal_location not in state.locations:
        raise ValueError(f"Unknown goal location: {goal_location}")

    if goal_type not in {"navigation", "retrieval"}:
        raise ValueError(f"Unknown goal type: {goal_type}")

    if goal_type == "retrieval":
        if goal_object is None:
            raise ValueError("Retrieval goals require goal_object")

        if goal_object not in object_names:
            raise ValueError(f"Unknown goal object: {goal_object}")
    lines = [
        f"(define (problem {problem_name})",
        f"  (:domain {DOMAIN_NAME})",
        "",
        "  (:objects",
    ]

    for location in state.locations:
        lines.append(
            f"    {location} - location"
        )

    for obj in state.objects:
        lines.append(
            f"    {obj.name} - object"
        )

    lines.extend([
        "  )",
        "",
        "  (:init",
        f"    (robot-at {state.robot_at})",
        "",
    ])

    for source, destination in state.connections:
        lines.append(
            f"    (connected {source} {destination})"
        )

    lines.append("")

    for obj in state.objects:
        lines.append(
            f"    (located {obj.name} {obj.location})"
        )

        if obj.on is not None:
            lines.append(
                f"    (on {obj.name} {obj.on})"
            )

        if obj.manipulable:
            lines.append(
                f"    (manipulable {obj.name})"
            )

    lines.append("  )")
    lines.append("")
    lines.append("  (:goal")

    if goal_type == "navigation":
        lines.append(f"    (robot-at {goal_location})")
    else:
        lines.append(f"    (located {goal_object} {goal_location})")

    lines.extend([
        "  )",
        ")",
        "",
    ])
    return "\n".join(lines)


def save_ground_truth_problem(
    state: SceneState,
    path: str | Path,
    goal_location: str,
    goal_object: str | None = None,
    goal_type: str = "retrieval",
    problem_name: str = "ground_truth",
) -> None:
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pddl = ground_truth_problem(
        state=state,
        goal_location=goal_location,
        goal_object=goal_object,
        goal_type=goal_type,
        problem_name=problem_name,
    )

    path.write_text(pddl)
