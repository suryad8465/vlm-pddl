"""Phase 3 evaluation runner (no-image ablation condition).

Evaluates the VLM on task instructions using only text prompts (no image input),
testing the model's reliance on visual observations versus linguistic priors.
Results are saved to ``experiments/phase3/no_image/<run_id>/``.
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from pipeline.phase3.prompt import build_phase3_prompt


MODEL = "qwen/qwen3.8-27b"

DOMAIN_FILE = Path("domain/household.pddl")
FAST_DOWNWARD = Path.home() / "downward" / "fast-downward.py"
VAL = Path.home() / "VAL" / "build" / "bin" / "Validate"


client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
def run_val(
    domain: Path,
    ground_truth_problem: Path,
    plan: Path,
    val_output_file: Path,
) -> dict:
    """Validate an execution plan against the ground-truth problem using VAL.

    Args:
        domain: Path to the PDDL domain file.
        ground_truth_problem: Path to the scenario's ground-truth PDDL problem.
        plan: Path to the generated SAS plan file to validate.
        val_output_file: Path where the raw stdout/stderr of VAL will be written.

    Returns:
        A dict containing val_valid (bool), val_timeout (bool), val_returncode,
        val_output (str), and val_latency_seconds (float).
    """

    start = time.perf_counter()

    try:
        result = subprocess.run(
            [
                str(VAL),
                str(domain),
                str(ground_truth_problem),
                str(plan),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {
            "val_valid": False,
            "val_timeout": True,
            "val_returncode": None,
            "val_output": "",
            "val_latency_seconds": (
                time.perf_counter() - start
            ),
        }

    elapsed = time.perf_counter() - start

    output = result.stdout + result.stderr

    val_output_file.write_text(output)

    # VAL's return code is not the validity criterion.
    # The Phase 2 validation procedure defines validity
    # by the presence of "Plan valid" in the output.
    valid = "Plan valid" in output

    return {
        "val_valid": valid,
        "val_timeout": False,
        "val_returncode": result.returncode,
        "val_output": output,
        "val_latency_seconds": elapsed,
    }

def encode_image(path: Path) -> str:
    """Base64-encode an image file and return the decoded ASCII string.

    Args:
        path: Path to the image file.

    Returns:
        Base64-encoded string representation of the image.
    """
    with path.open("rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


def clean_response(text: str) -> str:
    """Remove common reasoning tags (<think>...</think>) and code fences before parsing.

    Args:
        text: Raw response string from the VLM.

    Returns:
        Cleaned response text.
    """

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
    """Parse STATUS from the cleaned VLM response.

    Extracts either STATUS: PDDL (with accompanying PDDL problem body) or
    STATUS: CLARIFICATION_REQUIRED (with reason message).

    Args:
        text: Response text from the VLM.

    Returns:
        A dict with status ("PDDL", "CLARIFICATION_REQUIRED", or "PARSE_ERROR"),
        pddl (str or None), reason (str or None), and cleaned_response (str).
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


def load_scenario(scenario_id: str) -> dict:
    """Load scenario metadata, instruction text, and scene image path.

    Args:
        scenario_id: Scenario identifier, e.g. "scenario_001".

    Returns:
        Dict containing scenario_dir, metadata, instruction, and image path.

    Raises:
        FileNotFoundError: If the scenario directory does not exist.
    """
    scenario_dir = Path("scenarios") / scenario_id

    if not scenario_dir.exists():
        raise FileNotFoundError(
            f"Scenario not found: {scenario_dir}"
        )

    scenario_file = scenario_dir / "scenario.json"
    instruction_file = scenario_dir / "instruction.txt"
    image_file = scenario_dir / "scene.png"

    with scenario_file.open() as f:
        metadata = json.load(f)

    instruction = instruction_file.read_text().strip()

    return {
        "scenario_dir": scenario_dir,
        "metadata": metadata,
        "instruction": instruction,
        "image": image_file,
    }


def expected_status(metadata: dict) -> str:
    """Determine expected status under the Phase 3 ambiguity policy.

    precise -> PDDL
    novel   -> PDDL
    ambiguous -> CLARIFICATION_REQUIRED

    Args:
        metadata: Scenario metadata dict containing "instruction_style".

    Returns:
        "CLARIFICATION_REQUIRED" if style is ambiguous, otherwise "PDDL".
    """

    if metadata["instruction_style"] == "ambiguous":
        return "CLARIFICATION_REQUIRED"

    return "PDDL"


def query_vlm(
    domain_text: str,
    instruction: str,
) -> tuple[str, float]:
    """Query the VLM with a text-only prompt (no image).

    Args:
        domain_text: String content of the household PDDL domain.
        instruction: Natural-language task instruction.

    Returns:
        A tuple of (raw_output_text, latency_seconds).

    Raises:
        RuntimeError: If the VLM response contains no content.
    """

    prompt = build_phase3_prompt(
        domain_text=domain_text,
        instruction=instruction,
    )

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
        temperature=0,
        max_tokens=1000,
        reasoning_effort="none",
    )

    elapsed = time.perf_counter() - start

    output = response.choices[0].message.content

    if output is None:
        raise RuntimeError(
            "VLM returned no message content."
        )

    return output, elapsed


def run_planner(
    domain: Path,
    problem: Path,
    plan_output: Path,
) -> dict:
    """Run Fast Downward to find an optimal plan for the predicted problem.

    Executes A* search with lmcut heuristic, writes the plan to ``plan_output``
    if found, and extracts solvability and cost metrics.

    Args:
        domain: Path to the household domain PDDL file.
        problem: Path to the predicted problem PDDL file.
        plan_output: Destination path to write the SAS plan.

    Returns:
        A dict containing planner_solvable (bool), planner_timeout (bool),
        planner_returncode, planner_output, planner_latency_seconds, plan_length,
        and plan_cost.
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
        plan_output.write_text(
            sas_plan.read_text()
        )

    return {
        "planner_solvable": solvable,
        "planner_timeout": False,
        "planner_returncode": result.returncode,
        "planner_output": output,
        "planner_latency_seconds": elapsed,
        "plan_length": plan_length,
        "plan_cost": plan_cost,
    }


def main():
    """CLI entry point for Phase 3 no-image ablation evaluation.

    Parses scenario_id and run_id flags, evaluates using text-only prompts,
    solves and validates plans when PDDL is produced, and writes results to
    the no_image experiment directory.
    """
    parser = argparse.ArgumentParser(
        description="Run one Phase 3 VLM evaluation."
    )

    parser.add_argument(
        "scenario_id",
        help="For example: scenario_001",
    )
    parser.add_argument(
        "--run-id",
        default="run_001",
        help="Experiment run identifier, for example: run_002",
    )
    args = parser.parse_args()
    run_dir = (
        Path("experiments")
        / "phase3"
        / "no_image"
        / args.run_id
    )

    raw_dir = run_dir / "raw"
    pddl_dir = run_dir / "pddl"
    plan_dir = run_dir / "plans"
    val_dir = run_dir / "val"

    raw_dir.mkdir(parents=True, exist_ok=True)
    pddl_dir.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit(
            "ERROR: GROQ_API_KEY environment variable is not set."
        )

    if not DOMAIN_FILE.exists():
        raise SystemExit(
            f"ERROR: Domain file not found: {DOMAIN_FILE}"
        )

    if not FAST_DOWNWARD.exists():
        raise SystemExit(
            f"ERROR: Fast Downward not found: {FAST_DOWNWARD}"
        )
    if not VAL.exists():
        raise SystemExit(
            f"ERROR: VAL not found: {VAL}"
        )

    scenario = load_scenario(args.scenario_id)

    domain_text = DOMAIN_FILE.read_text()

    scenario_id = args.scenario_id
    metadata = scenario["metadata"]
    instruction = scenario["instruction"]
    image_path = scenario["image"]

    expected = expected_status(metadata)


    timestamp = datetime.now(timezone.utc).isoformat()

    print(f"Scenario: {scenario_id}")
    print(f"Instruction: {instruction}")
    print(f"Instruction style: {metadata['instruction_style']}")
    print(f"Expected status: {expected}")
    print(f"Model: {MODEL}")
    print()
    print("Sending instruction + domain to VLM (no image)...")

    try:
        raw_response, latency = query_vlm(
            domain_text=domain_text,
            instruction=instruction,
        )
    except Exception as exc:
        print()
        print("VLM ERROR:")
        print(exc)

        raw_file = raw_dir / f"{scenario_id}.txt"
        raw_file.write_text("")

        result = {
            "scenario_id": scenario_id,
            "condition": "no_image",
            "timestamp_utc": timestamp,
            "model": MODEL,
            "temperature": 0,
            "prompt_version": "phase3-v2",
            "instruction": instruction,
            "instruction_style": metadata["instruction_style"],
            "task_type": metadata["task_type"],
            "layout": metadata["layout"],
            "expected_status": expected,
            "predicted_status": None,
            "clarification_reason": None,
            "latency_seconds": None,
            "raw_response": str(raw_file),
            "predicted_pddl": None,
            "predicted_plan": None,
            "api_error": True,
            "api_error_message": str(exc),
            "empty_response": False,
        }

        result_file = raw_dir / f"{scenario_id}.result.json"
        result_file.write_text(
            json.dumps(
                result,
                indent=2,
            )
        )

        raise SystemExit(1)
    parsed = parse_response(raw_response)
    empty_response = not raw_response.strip()

    raw_file = raw_dir / f"{scenario_id}.txt"
    raw_file.write_text(raw_response)

    pddl_file = None
    plan_file = None

    planner_result = {
        "planner_solvable": None,
        "planner_timeout": False,
        "planner_returncode": None,
        "planner_output": "",
        "planner_latency_seconds": None,
        "plan_length": None,
        "plan_cost": None,
    }
    val_result = {
        "val_valid": None,
        "val_timeout": False,
        "val_returncode": None,
        "val_output": "",
        "val_latency_seconds": None,
    }

    if parsed["status"] == "PDDL":

        pddl_file = pddl_dir / f"{scenario_id}.pddl"
        pddl_file.write_text(parsed["pddl"])

        plan_file = plan_dir / f"{scenario_id}.plan"

        print()
        print("Running Fast Downward...")

        planner_result = run_planner(
            domain=DOMAIN_FILE,
            problem=pddl_file,
            plan_output=plan_file,
        )

        print(
            "Planner solvable:",
            planner_result["planner_solvable"],
        )

        if planner_result["plan_length"] is not None:
            print(
                "Plan length:",
                planner_result["plan_length"],
            )

        if planner_result["plan_cost"] is not None:
            print(
                "Plan cost:",
                planner_result["plan_cost"],
            )

        if plan_file.exists():
            print(f"Plan saved to: {plan_file}")
        if plan_file.exists():
            ground_truth_problem = (
                scenario["scenario_dir"] / "gt_problem.pddl"
            )

            val_file = val_dir / f"{scenario_id}.txt"

            print()
            print("Running VAL against ground-truth problem...")

            val_result = run_val(
                domain=DOMAIN_FILE,
                ground_truth_problem=ground_truth_problem,
                plan=plan_file,
                val_output_file=val_file,
            )

            print(
                "VAL valid:",
                val_result["val_valid"],
            )
            print(
                "VAL output saved to:",
                val_file,
            )
    result = {
        "scenario_id": scenario_id,
        "condition": "no_image",
        "timestamp_utc": timestamp,
        "model": MODEL,
        "temperature": 0,
        "prompt_version": "phase3-v2",
        "instruction": instruction,
        "instruction_style": metadata["instruction_style"],
        "task_type": metadata["task_type"],
        "layout": metadata["layout"],
        "expected_status": expected,
        "predicted_status": parsed["status"],
        "api_error": False,
        "empty_response": empty_response,
        "clarification_reason": parsed["reason"],
        "latency_seconds": latency,
        "raw_response": str(raw_file),
        "predicted_pddl": (
            str(pddl_file)
            if pddl_file is not None
            else None
        ),
        "predicted_plan": (
            str(plan_file)
            if plan_file is not None
            and plan_file.exists()
            else None
        ),
        **planner_result,
        **val_result,
    }

    result_file = (
        raw_dir / f"{scenario_id}.result.json"
    )

    result_file.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print()
    print("Raw response:")
    print("----------------------------------------")
    print(raw_response)
    print("----------------------------------------")

    print()
    print(f"Parsed status: {parsed['status']}")
    print(f"Expected status: {expected}")
    print(f"VLM latency: {latency:.3f} seconds")
    print(f"Raw response saved to: {raw_file}")
    print(f"Run metadata saved to: {result_file}")


if __name__ == "__main__":
    main()
