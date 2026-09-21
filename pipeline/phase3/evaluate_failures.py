from __future__ import annotations

import json
import sys
from pathlib import Path

from pipeline.phase3.evaluate_state import evaluate


FAILURE_PRIORITY = (
    "api_error",
    "empty_response",
    "parse_error",
    "invalid_pddl",
    "clarification_mismatch",
    "wrong_goal",
    "missing_fact",
    "hallucinated_fact",
    "planner_unsolvable",
    "val_invalid",
)


def load_result(path: Path) -> dict:
    return json.loads(path.read_text())


def classify_failure(
    result: dict,
    state_metrics: dict | None = None,
) -> dict:
    flags = {
        "api_error": False,
        "empty_response": False,
        "parse_error": False,
        "invalid_pddl": False,
        "clarification_mismatch": False,
        "wrong_goal": False,
        "missing_fact": False,
        "hallucinated_fact": False,
        "planner_unsolvable": False,
        "val_invalid": False,
    }

    predicted_status = result.get("predicted_status")
    expected_status = result.get("expected_status")

    raw_response = result.get("raw_response")
    predicted_pddl = result.get("predicted_pddl")

    # API failure recorded by the runner.
    if result.get("api_error"):
        flags["api_error"] = True

    # Empty response.
    if result.get("empty_response") is True:
        flags["empty_response"] = True
    elif raw_response:
        raw_path = Path(raw_response)
        if raw_path.exists() and not raw_path.read_text().strip():
            flags["empty_response"] = True
    elif predicted_status is None:
        flags["empty_response"] = True
    # Expected-status mismatch.
    if (
        predicted_status is not None
        and expected_status is not None
        and predicted_status != expected_status
    ):
        flags["clarification_mismatch"] = True

    # PDDL expected but no predicted PDDL was produced.
    if predicted_status == "PDDL" and not predicted_pddl:
        flags["parse_error"] = True

    # Planner failure.
    if (
        predicted_status == "PDDL"
        and result.get("planner_returncode") not in (None, 0)
    ):
        planner_output = result.get("planner_output", "")

        parse_markers = (
            "Undefined object",
            "Parsing problem",
            "translate exit code:",
            "Driver aborting after translate",
        )

        if any(
            marker in planner_output
            for marker in parse_markers
        ):
            flags["invalid_pddl"] = True
        else:
            flags["planner_unsolvable"] = True

    # Semantic state/goal failures are only trusted when the
    # generated PDDL successfully passed the planner.
    if (
        state_metrics
        and state_metrics.get("scoreable")
        and result.get("planner_returncode") == 0
    ):
        if not state_metrics.get("goal_exact_match", True):
            flags["wrong_goal"] = True

        initial_state = state_metrics.get(
            "initial_state",
            {},
        )

        if initial_state.get("fn", 0) > 0:
            flags["missing_fact"] = True

        if initial_state.get("fp", 0) > 0:
            flags["hallucinated_fact"] = True

    # VAL failure.
    if result.get("val_valid") is False:
        flags["val_invalid"] = True
    # Primary task-level outcome.
    task_success = False

    if expected_status == "CLARIFICATION_REQUIRED":
        task_success = (
            predicted_status == "CLARIFICATION_REQUIRED"
        )

    elif expected_status == "PDDL":
        task_success = (
            predicted_status == "PDDL"
            and result.get("planner_returncode") == 0
            and state_metrics is not None
            and state_metrics.get("goal_exact_match") is True
            and result.get("val_valid") is True
        )
    primary_failure = None

    for category in FAILURE_PRIORITY:
        if flags[category]:
            primary_failure = category
            break

    return {
        "task_success": task_success,
        "failure_flags": flags,
        "primary_failure": primary_failure,
        "failure_priority": list(FAILURE_PRIORITY),
    }

def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage: python pipeline/phase3/evaluate_failures.py "
            "<result.json>"
        )
        return 1

    repo_root = Path(__file__).resolve().parents[2]
    result_path = Path(sys.argv[1])

    if not result_path.is_absolute():
        result_path = repo_root / result_path

    if not result_path.exists():
        raise SystemExit(
            f"Result file not found: {result_path}"
        )

    result = load_result(result_path)

    scenario_id = result["scenario_id"]

    gt_path = (
        repo_root
        / "scenarios"
        / scenario_id
        / "gt_problem.pddl"
    )

    predicted_pddl_value = result.get(
        "predicted_pddl"
    )

    state_metrics = None

    if (
        result.get("predicted_status") == "PDDL"
        and predicted_pddl_value
    ):
        predicted_path = Path(predicted_pddl_value)

        if not predicted_path.is_absolute():
            predicted_path = repo_root / predicted_path

        state_metrics = evaluate(
            scenario_id=scenario_id,
            gt_path=gt_path,
            predicted_path=predicted_path,
            result_path=result_path,
        )

    classification = classify_failure(
        result,
        state_metrics=state_metrics,
    )

    output = {
        "scenario_id": scenario_id,
        "condition": result.get("condition", "normal"),
        **classification,
    }

    if state_metrics is not None:
        output["state_scoreable"] = state_metrics.get(
            "scoreable"
        )
        output["state_exact_match"] = state_metrics.get(
            "state_exact_match"
        )
        output["goal_exact_match"] = state_metrics.get(
            "goal_exact_match"
        )

    print(json.dumps(output, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
