import re
import subprocess
import sys
import time
from pathlib import Path


FAST_DOWNWARD = Path.home() / "downward" / "fast-downward.py"


def clean_response(text: str) -> str:
    """Remove common reasoning/formatting wrappers before parsing."""

    text = text.strip()

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    text = text.strip()

    match = re.search(
        r"```(?:pddl|lisp)?\s*(.*?)```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if match:
        text = match.group(1).strip()

    return text


def parse_response(text: str) -> dict:
    """
    Parse STATUS from a VLM response.

    This follows the Phase 3 response format without using
    ground truth.
    """

    cleaned = clean_response(text)

    status_match = re.search(
        r"^\s*STATUS\s*:\s*(PDDL|CLARIFICATION_REQUIRED)\s*$",
        cleaned,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    if not status_match:
        return {
            "status": "PARSE_ERROR",
            "pddl": None,
            "reason": "No valid STATUS line found.",
            "cleaned_response": cleaned,
        }

    status = status_match.group(1).upper()
    remainder = cleaned[status_match.end():].strip()

    if status == "PDDL":
        if not remainder:
            return {
                "status": "PARSE_ERROR",
                "pddl": None,
                "reason": "STATUS:PDDL was returned without PDDL.",
                "cleaned_response": cleaned,
            }

        return {
            "status": "PDDL",
            "pddl": remainder,
            "reason": None,
            "cleaned_response": cleaned,
        }

    return {
        "status": "CLARIFICATION_REQUIRED",
        "pddl": None,
        "reason": remainder,
        "cleaned_response": cleaned,
    }


def run_planner(
    domain: Path,
    problem: Path,
    plan_output: Path,
) -> dict:
    """
    Run Fast Downward as the deployment-time pipeline check.

    No ground-truth problem is used here.
    """

    start = time.perf_counter()

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(FAST_DOWNWARD),
                str(domain),
                str(problem),
                "--search",
                "astar(lmcut())",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {
            "planner_solvable": False,
            "planner_timeout": True,
            "planner_returncode": None,
            "planner_output": "",
            "planner_latency_seconds": (
                time.perf_counter() - start
            ),
            "plan_length": None,
            "plan_cost": None,
        }

    elapsed = time.perf_counter() - start
    output = result.stdout + result.stderr

    solvable = "Solution found." in output

    plan_length = None
    plan_cost = None

    length_match = re.search(
        r"Plan length:\s*(\d+)\s*step",
        output,
    )

    if length_match:
        plan_length = int(length_match.group(1))

    cost_match = re.search(
        r"Plan cost:\s*([0-9]+(?:\.[0-9]+)?)",
        output,
    )

    if cost_match:
        plan_cost = float(cost_match.group(1))

    sas_plan = Path("sas_plan")

    if solvable and sas_plan.exists():
        plan_output.write_text(sas_plan.read_text())

    return {
        "planner_solvable": solvable,
        "planner_timeout": False,
        "planner_returncode": result.returncode,
        "planner_output": output,
        "planner_latency_seconds": elapsed,
        "plan_length": plan_length,
        "plan_cost": plan_cost,
    }


def evaluate_candidate(
    domain: Path,
    pddl_text: str,
    work_dir: Path,
    candidate_name: str,
) -> dict:
    """
    Evaluate a generated PDDL candidate using only deployment-time checks.

    Ground truth is deliberately not accepted as an argument.
    """

    work_dir.mkdir(parents=True, exist_ok=True)

    pddl_path = work_dir / f"{candidate_name}.pddl"
    plan_path = work_dir / f"{candidate_name}.plan"

    pddl_path.write_text(pddl_text)

    planner_result = run_planner(
        domain=domain,
        problem=pddl_path,
        plan_output=plan_path,
    )

    return {
        "pddl_path": str(pddl_path),
        "plan_path": (
            str(plan_path)
            if plan_path.exists()
            else None
        ),
        **planner_result,
    }

