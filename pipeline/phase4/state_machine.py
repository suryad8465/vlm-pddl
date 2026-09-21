from dataclasses import dataclass
from enum import Enum


class FeedbackMode(str, Enum):
    DEPLOYMENT = "DEPLOYMENT"
    O1 = "O1"


class Decision(str, Enum):
    STOP_SUCCESS = "STOP_SUCCESS"
    REFINE = "REFINE"
    STOP_FAILURE = "STOP_FAILURE"


@dataclass(frozen=True)
class DeploymentSignals:
    """Signals available without ground truth."""

    expected_clarification: bool = False
    predicted_clarification: bool = False
    parser_ok: bool = False
    planner_ok: bool = False
    verifier_consistent: bool | None = None
    pipeline_error: bool = False


@dataclass(frozen=True)
class OracleSignals:
    """Oracle-derived signals.

    These are permitted only in oracle feedback conditions such as O1.
    They must never be passed into deployment-only prompt construction.
    """

    failure_detected: bool = False


def decide(
    *,
    mode: FeedbackMode,
    deployment: DeploymentSignals,
    attempts_used: int,
    max_attempts: int = 4,
    oracle: OracleSignals | None = None,
) -> Decision:
    """Decide whether to stop or refine.

    DEPLOYMENT mode:
        Uses parser/planner/pipeline signals only.

    O1 mode:
        The oracle verdict is both feedback and stopping information.
        Ground-truth scoring itself remains outside prompt construction.

    This function never receives a ground-truth PDDL problem.
    """

    if attempts_used < 1:
        raise ValueError("attempts_used must be at least 1.")

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    if attempts_used > max_attempts:
        raise ValueError(
            "attempts_used cannot exceed max_attempts."
        )

    if mode == FeedbackMode.O1:
        if oracle is None:
            raise ValueError(
                "O1 mode requires OracleSignals."
            )

        if oracle.failure_detected:
            if attempts_used < max_attempts:
                return Decision.REFINE
            return Decision.STOP_FAILURE

        return Decision.STOP_SUCCESS

    if mode != FeedbackMode.DEPLOYMENT:
        raise ValueError(f"Unsupported feedback mode: {mode}")

    if deployment.expected_clarification:
        return Decision.STOP_SUCCESS

    if deployment.predicted_clarification:
        return Decision.STOP_FAILURE

    detected_failure = (
        deployment.pipeline_error
        or not deployment.parser_ok
        or not deployment.planner_ok
        or deployment.verifier_consistent is False
    )

    if detected_failure:
        if attempts_used < max_attempts:
            return Decision.REFINE
        return Decision.STOP_FAILURE

    deployment_success = (
        deployment.parser_ok
        and deployment.planner_ok
        and not deployment.pipeline_error
    )

    verifier_success = (
        deployment.verifier_consistent is True
        and not deployment.pipeline_error
    )

    if deployment_success or verifier_success:
        return Decision.STOP_SUCCESS

    return Decision.STOP_FAILURE
