from __future__ import annotations

import json
import re
import sys
from pathlib import Path


PREDICATES = (
    "robot-at",
    "connected",
    "located",
    "on",
    "holding",
    "manipulable",
)

OBSERVABILITY = {
    "robot-at": "VISUAL_PLUS_SEMANTIC",
    "connected": "VISUAL_PLUS_SEMANTIC",
    "located": "VISUAL_PLUS_SEMANTIC",
    "on": "DIRECT_VISUAL",
    "holding": "VISUAL_PLUS_SEMANTIC",
    "manipulable": "SEMANTIC_DOMAIN",
}


def extract_section(text: str, section: str) -> str:
    """Extract the contents of a named PDDL section."""
    match = re.search(
        rf"\(:{re.escape(section)}\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""

    start = match.end()
    depth = 1

    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start:i]

    raise ValueError(f"Unclosed PDDL section: {section}")


def parse_facts(section_text: str) -> set[tuple[str, tuple[str, ...]]]:
    """Parse simple positive PDDL facts from a section."""
    facts = set()

    for match in re.finditer(r"\(([^()]+)\)", section_text):
        tokens = match.group(1).split()
        if not tokens:
            continue

        predicate = tokens[0]
        args = tuple(tokens[1:])

        if predicate in PREDICATES:
            facts.add((predicate, args))

    return facts


def load_pddl(path: Path) -> tuple[set, set]:
    text = path.read_text()

    init_text = extract_section(text, "init")
    goal_text = extract_section(text, "goal")

    return parse_facts(init_text), parse_facts(goal_text)


def f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
def format_metric(value) -> str:
    if value is None:
        return "N/A"
    return f"{value:.3f}"

def score_sets(
    predicted: set,
    ground_truth: set,
) -> dict:
    tp = len(predicted & ground_truth)
    fp = len(predicted - ground_truth)
    fn = len(ground_truth - predicted)

    precision = (
        tp / (tp + fp)
        if tp + fp
        else None
    )

    recall = (
        tp / (tp + fn)
        if tp + fn
        else None
    )

    if precision is None or recall is None:
        f1_score = None
    else:
        f1_score = f1(precision, recall)

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1_score,
    }

def evaluate(
    scenario_id: str,
    gt_path: Path,
    predicted_path: Path,
    result_path: Path,
) -> dict:
    result = {
        "scenario_id": scenario_id,
        "scoreable": False,
        "reason": None,
        "observability_classes": OBSERVABILITY,
    }
    if not result_path.exists():
        result["reason"] = (
            f"missing Phase 3 result metadata: {result_path}"
        )
        return result

    try:
        run_result = json.loads(
            result_path.read_text()
        )
    except Exception as exc:
        result["reason"] = (
            f"result_metadata_parse_error: {exc}"
        )
        return result

    predicted_status = run_result.get(
        "predicted_status"
    )

    result["predicted_status"] = predicted_status
    result["expected_status"] = run_result.get(
        "expected_status"
    )
    if predicted_status != "PDDL":
        result["reason"] = (
            f"current VLM status is {predicted_status}; "
            "predicted PDDL is not scoreable"
        )
        return result
    if not gt_path.exists():
        result["reason"] = f"missing ground truth: {gt_path}"
        return result

    if not predicted_path.exists():
        result["reason"] = f"missing predicted PDDL: {predicted_path}"
        return result

    try:
        gt_init, gt_goal = load_pddl(gt_path)
        predicted_init, predicted_goal = load_pddl(predicted_path)
    except Exception as exc:
        result["reason"] = f"pddl_parse_error: {exc}"
        return result

    result["scoreable"] = True

    # Full initial-state comparison.
    state_metrics = score_sets(predicted_init, gt_init)

    # Goal comparison is exact-set comparison.
    goal_metrics = score_sets(predicted_goal, gt_goal)

    result["state_exact_match"] = predicted_init == gt_init
    result["goal_exact_match"] = predicted_goal == gt_goal

    result["initial_state"] = state_metrics
    result["goal"] = goal_metrics

    # Per-predicate initial-state metrics.
    per_predicate = {}

    for predicate in PREDICATES:
        gt_facts = {
            fact for fact in gt_init
            if fact[0] == predicate
        }
        predicted_facts = {
            fact for fact in predicted_init
            if fact[0] == predicate
        }

        metrics = score_sets(predicted_facts, gt_facts)
        metrics["observability"] = OBSERVABILITY[predicate]
        metrics["gt_count"] = len(gt_facts)
        metrics["predicted_count"] = len(predicted_facts)

        per_predicate[predicate] = metrics

    result["per_predicate"] = per_predicate

    # Aggregate by observability class.
    by_class = {}

    for predicate in PREDICATES:
        cls = OBSERVABILITY[predicate]

        if cls not in by_class:
            by_class[cls] = {
                "tp": 0,
                "fp": 0,
                "fn": 0,
                "predicates": [],
            }

        metrics = per_predicate[predicate]

        by_class[cls]["tp"] += metrics["tp"]
        by_class[cls]["fp"] += metrics["fp"]
        by_class[cls]["fn"] += metrics["fn"]
        by_class[cls]["predicates"].append(predicate)

    for cls, metrics in by_class.items():
        tp = metrics["tp"]
        fp = metrics["fp"]
        fn = metrics["fn"]

        precision = (
            tp / (tp + fp)
            if tp + fp
            else None
        )

        recall = (
            tp / (tp + fn)
            if tp + fn
            else None
        )

        if precision is None or recall is None:
            f1_score = None
        else:
            f1_score = f1(precision, recall)

        metrics["precision"] = precision
        metrics["recall"] = recall
        metrics["f1"] = f1_score
    result["by_observability"] = by_class

    return result


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: python pipeline/phase3/evaluate_state.py "
            "SCENARIO_ID [SCENARIO_ID ...]"
        )
        return 1

    repo_root = Path(__file__).resolve().parents[2]

    for scenario_id in sys.argv[1:]:
        gt_path = (
            repo_root
            / "scenarios"
            / scenario_id
            / "gt_problem.pddl"
        )

        predicted_path = (
            repo_root
            / "experiments"
            / "phase3"
            / "pddl"
            / f"{scenario_id}.pddl"
        )
        result_path = (
            repo_root
            / "experiments"
            / "phase3"
            / "raw"
            / f"{scenario_id}.result.json"
        )
        result = evaluate(
            scenario_id,
            gt_path,
            predicted_path,
            result_path,
        )

        output_path = (
            repo_root
            / "experiments"
            / "phase3"
            / "raw"
            / f"{scenario_id}_state_metrics.json"
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2) + "\n"
        )

        print(f"\n=== {scenario_id} ===")
        print(
            f"Predicted status: "
            f"{result.get('predicted_status', 'N/A')}"
        )
        print(f"Scoreable: {result['scoreable']}")
        if not result["scoreable"]:
            print(f"Reason: {result['reason']}")
            continue

        print(
            f"State exact match: "
            f"{result['state_exact_match']}"
        )
        print(
            f"Goal exact match: "
            f"{result['goal_exact_match']}"
        )

        print("\nPer-predicate:")
        for predicate, metrics in result["per_predicate"].items():
            print(
                f"  {predicate:12s} "
                f"obs={metrics['observability']:22s} "
                f"TP={metrics['tp']} "
                f"FP={metrics['fp']} "
                f"FN={metrics['fn']} "
                f"F1={format_metric(metrics['f1'])}"
            )

        print("\nBy observability:")
        for cls, metrics in result["by_observability"].items():
            print(
                f"  {cls:22s} "
                f"TP={metrics['tp']} "
                f"FP={metrics['fp']} "
                f"FN={metrics['fn']} "
                f"F1={format_metric(metrics['f1'])}"

            )

        print(f"\nSaved: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
