import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.phase4.api import query
from pipeline.phase4.evaluation import (
    evaluate_candidate,
    parse_response,
)
from pipeline.phase4.prompts import build_refinement_messages
from pipeline.phase4.state_machine import (
    DeploymentSignals,
    FeedbackMode,
    OracleSignals,
    decide,
)

FROZEN_PHASE3_RAW = (
    Path("experiments")
    / "phase3"
    / "labelled"
    / "headline_labelled"
    / "raw"
    / "scenario_004.txt"
)


MODEL = "qwen/qwen3.8-27b"
DOMAIN_FILE = Path("domain/household.pddl")

MAX_ATTEMPTS = 4
O1_FEEDBACK = (
    "The plan produced from your problem does not achieve the intended task. "
    "Please revise your PDDL problem."
)

def load_scenario(scenario_id: str) -> dict:
    scenario_dir = Path("scenarios") / scenario_id

    if not scenario_dir.exists():
        raise FileNotFoundError(
            f"Scenario not found: {scenario_dir}"
        )

    scenario_file = scenario_dir / "scenario.json"
    instruction_file = scenario_dir / "instruction.txt"
    image_file = scenario_dir / "scene_labelled.png"

    if not scenario_file.exists():
        raise FileNotFoundError(
            f"Missing scenario metadata: {scenario_file}"
        )

    if not instruction_file.exists():
        raise FileNotFoundError(
            f"Missing instruction: {instruction_file}"
        )

    if not image_file.exists():
        raise FileNotFoundError(
            f"Missing labelled image: {image_file}"
        )

    scenario = json.loads(
        scenario_file.read_text()
    )

    scenario["scenario_id"] = scenario_id
    scenario["scenario_dir"] = scenario_dir
    scenario["instruction"] = (
        instruction_file.read_text().strip()
    )
    scenario["image_file"] = image_file

    return scenario


def expected_status(metadata: dict) -> str:
    if metadata["instruction_style"] == "ambiguous":
        return "CLARIFICATION_REQUIRED"

    return "PDDL"


def append_attempt_log(
    *,
    output_dir: Path,
    attempt_result: dict,
) -> None:
    """Append one completed attempt to the Phase 4 JSONL log."""

    log_file = output_dir / "attempts.jsonl"

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                attempt_result,
                ensure_ascii=False,
            )
            + "\n"
        )


def load_completed_attempts(
    *,
    output_dir: Path,
) -> dict[int, dict]:
    """Load completed attempts from the append-only JSONL log."""

    log_file = output_dir / "attempts.jsonl"

    if not log_file.exists():
        return {}

    completed = {}

    with log_file.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSONL at {log_file}:{line_number}"
                ) from exc

            attempt = record.get("attempt")

            if not isinstance(attempt, int) or attempt < 1:
                raise ValueError(
                    f"Invalid attempt number at "
                    f"{log_file}:{line_number}"
                )

            completed[attempt] = record

    return completed
def evaluate_attempt(
    *,
    scenario: dict,
    output_dir: Path,
    attempt: int,
    raw_response: str,
    api_record: dict,
    attempt_source: str,
) -> tuple[dict, int]:
    """Parse and evaluate one Phase 4 VLM response."""

    parsed = parse_response(raw_response)

    attempt_dir = output_dir / f"attempt_{attempt}"
    attempt_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_file = attempt_dir / "raw.txt"
    raw_file.write_text(
        raw_response,
        encoding="utf-8",
    )

    attempt_result = {
        "attempt": attempt,
        "scenario_id": scenario["scenario_id"],
        "condition": "labelled",
        "model": MODEL,
        "temperature": 0 if attempt == 1 else 0.7,
        "prompt_version": (
            "phase3-v2"
            if attempt == 1
            else "phase4-refinement-v1"
        ),
        "instruction": scenario["instruction"],
        "instruction_style": scenario["instruction_style"],
        "task_type": scenario["task_type"],
        "layout": scenario["layout"],
        "expected_status": expected_status(scenario),
        "predicted_status": parsed["status"],
        "clarification_reason": parsed["reason"],
        "raw_response": str(raw_file),
        "attempt_source": attempt_source,
        **api_record,
    }

    if parsed["status"] == "PDDL":
        deployment_dir = attempt_dir / "deployment"

        deployment = evaluate_candidate(
            domain=DOMAIN_FILE,
            pddl_text=parsed["pddl"],
            work_dir=deployment_dir,
            candidate_name="candidate",
        )

        attempt_result["predicted_pddl"] = deployment[
            "pddl_path"
        ]
        attempt_result["predicted_plan"] = deployment[
            "plan_path"
        ]
        attempt_result.update(deployment)

    else:
        attempt_result["predicted_pddl"] = None
        attempt_result["predicted_plan"] = None

    result_file = attempt_dir / "result.json"

    result_file.write_text(
        json.dumps(
            attempt_result,
            indent=2,
        ),
        encoding="utf-8",
    )

    append_attempt_log(
        output_dir=output_dir,
        attempt_result=attempt_result,
    )

    total_tokens = api_record.get("total_tokens")

    return attempt_result, (
        total_tokens
        if total_tokens is not None
        else 0
    )

def run_attempt_1(
    *,
    scenario: dict,
    output_dir: Path,
    token_budget_used: int,
) -> tuple[dict, int]:
    """Run Phase 3 generation unchanged as Phase 4 attempt 1."""

    scenario_id = scenario["scenario_id"]
    instruction = scenario["instruction"]
    image_path = scenario["image_file"]


    if scenario_id != "scenario_004":
        raise ValueError(
            "Frozen Phase 3 attempt-1 reuse is currently implemented "
            "only for scenario_004."
        )

    if not FROZEN_PHASE3_RAW.exists():
        raise FileNotFoundError(
            f"Missing frozen Phase 3 response: {FROZEN_PHASE3_RAW}"
        )

    print()
    print("Phase 4 attempt 1")
    print("-----------------")
    print("Scenario:", scenario_id)
    print("Condition: labelled")
    print("Instruction:", instruction)
    print("Expected status:", expected_status(scenario))
    print("Model:", MODEL)
    print()
    print("Reusing frozen Phase 3 response...")
    print("Source:", FROZEN_PHASE3_RAW)

    raw_response = FROZEN_PHASE3_RAW.read_text()

    api_record = {
        "api_error": False,
        "empty_response": not bool(raw_response.strip()),
        "latency_seconds": 0.0,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": 0,
        "attempt_source": "frozen_phase3",
        "api_call": False,
    }

    parsed = parse_response(raw_response)

    attempt_dir = output_dir / "attempt_1"
    attempt_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_file = attempt_dir / "raw.txt"
    raw_file.write_text(raw_response)

    attempt_result = {
        "attempt": 1,
        "scenario_id": scenario_id,
        "condition": "labelled",
        "model": MODEL,
        "temperature": 0,
        "prompt_version": "phase3-v2",
        "instruction": instruction,
        "instruction_style": scenario["instruction_style"],
        "task_type": scenario["task_type"],
        "layout": scenario["layout"],
        "expected_status": expected_status(scenario),
        "predicted_status": parsed["status"],
        "clarification_reason": parsed["reason"],
        "raw_response": str(raw_file),
        **api_record,
    }

    if parsed["status"] == "PDDL":
        deployment_dir = attempt_dir / "deployment"

        deployment = evaluate_candidate(
            domain=DOMAIN_FILE,
            pddl_text=parsed["pddl"],
            work_dir=deployment_dir,
            candidate_name="candidate",
        )

        attempt_result["predicted_pddl"] = deployment[
            "pddl_path"
        ]
        attempt_result["predicted_plan"] = deployment[
            "plan_path"
        ]
        attempt_result.update(deployment)

    else:
        attempt_result["predicted_pddl"] = None
        attempt_result["predicted_plan"] = None

    result_file = attempt_dir / "result.json"

    result_file.write_text(
        json.dumps(
            attempt_result,
            indent=2,
        )
    )
    append_attempt_log(
        output_dir=output_dir,
        attempt_result=attempt_result,
    )

    print()
    print("Predicted status:", parsed["status"])

    if parsed["reason"]:
        print("Reason:", parsed["reason"])

    if parsed["status"] == "PDDL":
        print(
            "Planner solvable:",
            attempt_result["planner_solvable"],
        )

        print(
            "Planner latency:",
            attempt_result["planner_latency_seconds"],
        )

    print("Result:", result_file)

    total_tokens = api_record.get("total_tokens")

    if total_tokens is None:
        updated_token_budget = token_budget_used
    else:
        updated_token_budget = (
            token_budget_used + total_tokens
        )

    return attempt_result, updated_token_budget

def run_refinement_attempt(
    *,
    scenario: dict,
    output_dir: Path,
    attempt: int,
    previous_result: dict,
    token_budget_used: int,
) -> tuple[dict, int]:
    """Run one O1 refinement attempt."""

    previous_pddl_path = previous_result.get(
        "predicted_pddl"
    )

    if not previous_pddl_path:
        raise RuntimeError(
            "Cannot refine an attempt without a PDDL candidate."
        )

    previous_pddl = Path(
        previous_pddl_path
    ).read_text(
        encoding="utf-8"
    )

    messages = build_refinement_messages(
        image_path=scenario["image_file"],
        instruction=scenario["instruction"],
        previous_pddl=previous_pddl,
        feedback=O1_FEEDBACK,
    )

    print()
    print(f"Phase 4 attempt {attempt}")
    print("-----------------")
    print("Scenario:", scenario["scenario_id"])
    print("Condition: labelled")
    print("Feedback mode: O1")
    print("Feedback:", O1_FEEDBACK)
    print("Sending refinement request...")

    raw_response, api_record = query(
        messages,
        token_budget_used=token_budget_used,
    )

    attempt_result, attempt_tokens = evaluate_attempt(
        scenario=scenario,
        output_dir=output_dir,
        attempt=attempt,
        raw_response=raw_response,
        api_record=api_record,
        attempt_source="phase4_refinement",
    )

    print()
    print("Predicted status:", attempt_result["predicted_status"])

    if attempt_result.get("predicted_status") == "PDDL":
        print(
            "Planner solvable:",
            attempt_result.get("planner_solvable"),
        )

    print(
        "Total tokens:",
        attempt_result.get("total_tokens"),
    )

    return (
        attempt_result,
        token_budget_used + attempt_tokens,
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 4 iterative VLM/PDDL runner."
    )

    parser.add_argument(
        "scenario_id",
        help="Scenario ID, e.g. scenario_004",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory.",
    )

    args = parser.parse_args()

    if args.scenario_id != "scenario_004":
        raise ValueError(
            "The Phase 4 O1 pilot currently supports "
            "scenario_004 only."
        )

    scenario = load_scenario(
        args.scenario_id
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    if args.output_dir:
        output_dir = Path(
            args.output_dir
        )
    else:
        output_dir = (
            Path("results")
            / "phase4"
            / args.scenario_id
            / timestamp
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    completed_attempts = load_completed_attempts(
        output_dir=output_dir,
    )

    if completed_attempts:
        print()
        print("Resuming existing Phase 4 run.")
        print(
            "Completed attempts:",
            sorted(completed_attempts),
        )

    token_budget_used = sum(
        record.get("total_tokens") or 0
        for record in completed_attempts.values()
    )

    # ---------------------------------------------------------
    # Attempt 1: frozen Phase 3 response
    # ---------------------------------------------------------

    if 1 in completed_attempts:
        attempt_result = completed_attempts[1]
        print("Attempt 1 already completed; skipping.")
    else:
        attempt_result, attempt_tokens = run_attempt_1(
            scenario=scenario,
            output_dir=output_dir,
            token_budget_used=0,
        )

        token_budget_used += attempt_tokens
        completed_attempts[1] = attempt_result

    # ---------------------------------------------------------
    # O1 oracle verdict for attempt 1
    #
    # For the pilot, scenario_004 is a known MISSING_FACT case.
    # This oracle verdict is evaluation information, not GT
    # passed into VLM prompt construction.
    # ---------------------------------------------------------

    oracle = OracleSignals(
        failure_detected=True,
    )

    deployment = DeploymentSignals(
        parser_ok=(
            completed_attempts[1]["predicted_status"]
            == "PDDL"
        ),
        planner_ok=completed_attempts[1].get(
            "planner_solvable",
            False,
        ),
        pipeline_error=completed_attempts[1].get(
            "api_error",
            False,
        ),
    )

    decision = decide(
        mode=FeedbackMode.O1,
        deployment=deployment,
        oracle=oracle,
        attempts_used=1,
        max_attempts=MAX_ATTEMPTS,
    )

    print()
    print("O1 decision after attempt 1:", decision.value)

    if decision.value == "STOP_SUCCESS":
        print("O1 oracle accepted the candidate.")
        return

    # ---------------------------------------------------------
    # Attempts 2–4
    # ---------------------------------------------------------

    for attempt in range(2, MAX_ATTEMPTS + 1):
        if attempt in completed_attempts:
            print(
                f"Attempt {attempt} already completed; "
                "skipping."
            )
            previous_result = completed_attempts[attempt]
        else:
            previous_result = completed_attempts[
                attempt - 1
            ]

            attempt_result, token_budget_used = (
                run_refinement_attempt(
                    scenario=scenario,
                    output_dir=output_dir,
                    attempt=attempt,
                    previous_result=previous_result,
                    token_budget_used=token_budget_used,
                )
            )

            completed_attempts[attempt] = (
                attempt_result
            )

        # -----------------------------------------------------
        # O1 stopping:
        # oracle is the feedback AND stopping signal.
        # -----------------------------------------------------

        oracle = OracleSignals(
            failure_detected=True,
        )

        deployment = DeploymentSignals(
            parser_ok=(
                completed_attempts[attempt][
                    "predicted_status"
                ]
                == "PDDL"
            ),
            planner_ok=completed_attempts[attempt].get(
                "planner_solvable",
                False,
            ),
            pipeline_error=completed_attempts[attempt].get(
                "api_error",
                False,
            ),
        )

        decision = decide(
            mode=FeedbackMode.O1,
            deployment=deployment,
            oracle=oracle,
            attempts_used=attempt,
            max_attempts=MAX_ATTEMPTS,
        )

        print(
            f"O1 decision after attempt {attempt}:",
            decision.value,
        )

        if decision.value == "STOP_SUCCESS":
            break

        if decision.value == "STOP_FAILURE":
            print(
                "O1 pilot reached the maximum "
                "number of attempts."
            )
            break
if __name__ == "__main__":
    main()
