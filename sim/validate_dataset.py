import re
import subprocess
from pathlib import Path


SCENARIOS_ROOT = Path("scenarios")
DOMAIN = Path("domain/household.pddl")
FAST_DOWNWARD = Path.home() / "downward" / "fast-downward.py"


def validate_scenario(scenario_dir: Path) -> dict:
    problem = scenario_dir / "gt_problem.pddl"

    result = subprocess.run(
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

    output = result.stdout + result.stderr

    plan_length = None
    plan_cost = None

    match = re.search(
        r"Plan length:\s+(\d+)\s+step\(s\)",
        output,
    )

    if match:
        plan_length = int(match.group(1))

    match = re.search(
        r"Plan cost:\s+(\d+)",
        output,
    )

    if match:
        plan_cost = int(match.group(1))

    return {
        "scenario": scenario_dir.name,
        "exit_code": result.returncode,
        "solved": "Solution found." in output,
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
            f"solved={result['solved']} | "
            f"length={result['plan_length']} | "
            f"cost={result['plan_cost']} | "
            f"exit={result['exit_code']}"
        )

    failures = [
        result
        for result in results
        if not result["solved"]
        or result["exit_code"] != 0
    ]

    print()
    print("Failures:", len(failures))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
