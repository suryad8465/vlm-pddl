import re
import shutil
import subprocess
from pathlib import Path


SCENARIOS_ROOT = Path("scenarios")
DOMAIN = Path("domain/household.pddl")
FAST_DOWNWARD = Path.home() / "downward" / "fast-downward.py"
VAL = Path.home() / "VAL" / "build" / "bin" / "Validate"


def validate_scenario(scenario_dir: Path) -> dict:
    problem = scenario_dir / "gt_problem.pddl"
    plan_file = scenario_dir / "plan.txt"

    planner = subprocess.run(
        [
            "python",
            str(FAST_DOWNWARD),
            str(DOMAIN),
            str(problem),
            "--search",
            "astar(lmcut())",
        ],
        capture_output=True,
        text=True,
    )

    planner_output = planner.stdout + planner.stderr

    if planner.returncode != 0 or "Solution found." not in planner_output:
        return {
            "scenario": scenario_dir.name,
            "planner_ok": False,
            "val_ok": False,
            "plan_length": None,
            "plan_cost": None,
        }

    plan_source = Path("sas_plan")

    if not plan_source.exists():
        return {
            "scenario": scenario_dir.name,
            "planner_ok": False,
            "val_ok": False,
            "plan_length": None,
            "plan_cost": None,
        }

    shutil.copy2(plan_source, plan_file)

    plan_length = None
    plan_cost = None

    match = re.search(
        r"Plan length:\s+(\d+)\s+step\(s\)",
        planner_output,
    )

    if match:
        plan_length = int(match.group(1))

    match = re.search(
        r"Plan cost:\s+(\d+)",
        planner_output,
    )

    if match:
        plan_cost = int(match.group(1))

    val = subprocess.run(
        [
            str(VAL),
            str(DOMAIN),
            str(problem),
            str(plan_file),
        ],
        capture_output=True,
        text=True,
    )

    val_output = val.stdout + val.stderr

    val_ok = "Plan valid" in val_output

    return {
        "scenario": scenario_dir.name,
        "planner_ok": True,
        "val_ok": val_ok,
        "plan_length": plan_length,
        "plan_cost": plan_cost,
    }


def main() -> None:
    scenarios = sorted(
        SCENARIOS_ROOT.glob("scenario_*")
    )

    results = [
        validate_scenario(scenario)
        for scenario in scenarios
    ]

    print("Scenarios checked:", len(results))
    print()

    for result in results:
        print(
            f"{result['scenario']} | "
            f"planner={result['planner_ok']} | "
            f"VAL={result['val_ok']} | "
            f"length={result['plan_length']} | "
            f"cost={result['plan_cost']}"
        )

    failures = [
        result
        for result in results
        if not result["planner_ok"]
        or not result["val_ok"]
    ]

    print()
    print("Validation failures:", len(failures))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
