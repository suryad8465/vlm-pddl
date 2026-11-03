"""Phase 4 iterative refinement stopping-criterion state machine.

Defines decision enums, signal containers (deployment-only vs. oracle-informed),
and the ``decide()`` function controlling loop continuation (REFINE, STOP_SUCCESS,
or STOP_FAILURE).
"""

from dataclasses import dataclass
from enum import Enum


class FeedbackMode(str, Enum):
    """Feedback modes for Phase 4 refinement loops.

    DEPLOYMENT: Relies only on parser, planner, and self-verifier signals.
    O1: Driven by an oracle failure detection signal.
    """

    DEPLOYMENT = "DEPLOYMENT"
    O1 = "O1"


class Decision(str, Enum):
    """Decision outcomes for each refinement step.

    STOP_SUCCESS: Task considered complete/valid; stop refinement loop.
    REFINE: Candidate has detected issues and attempts remain; continue refining.
    STOP_FAILURE: Max attempts reached or terminal failure detected; stop loop.
    """

    STOP_SUCCESS = "STOP_SUCCESS"
    REFINE = "REFINE"
    STOP_FAILURE = "STOP_FAILURE"


@dataclass(frozen=True)
class DeploymentSignals:
    """Signals available during deployment without ground truth.

    Attributes:
        expected_clarification: Whether the task expected a clarification request.
        predicted_clarification: Whether the model returned a clarification request.
        parser_ok: True if the candidate PDDL was successfully parsed.
        planner_ok: True if Fast Downward successfully solved the candidate PDDL.
        verifier_consistent: Self-verifier output (True=CONSISTENT, False=INCONSISTENT, None=not run).
        pipeline_error: True if an unhandled API or subprocess error occurred.
    """

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

    Attributes:
        failure_detected: True if an oracle detects semantic or planning failure.
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

    Args:
        mode: The active FeedbackMode (DEPLOYMENT or O1).
        deployment: DeploymentSignals observed from parser/planner/verifier.
        attempts_used: Number of attempts completed so far (1-indexed).
        max_attempts: Maximum permitted refinement attempts.
        oracle: Optional OracleSignals required when mode is O1.

    Returns:
        A Decision enum (STOP_SUCCESS, REFINE, or STOP_FAILURE).

    Raises:
        ValueError: If attempts_used or max_attempts is invalid, or if O1 mode
            is specified without OracleSignals.
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
