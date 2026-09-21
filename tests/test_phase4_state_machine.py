import pytest

from pipeline.phase4.state_machine import (
    Decision,
    DeploymentSignals,
    FeedbackMode,
    OracleSignals,
    decide,
)


def test_o1_success_stops():
    assert decide(
        mode=FeedbackMode.O1,
        deployment=DeploymentSignals(),
        oracle=OracleSignals(failure_detected=False),
        attempts_used=1,
    ) == Decision.STOP_SUCCESS


def test_o1_failure_refines():
    assert decide(
        mode=FeedbackMode.O1,
        deployment=DeploymentSignals(),
        oracle=OracleSignals(failure_detected=True),
        attempts_used=1,
    ) == Decision.REFINE


def test_o1_failure_on_attempt_4_stops_failure():
    assert decide(
        mode=FeedbackMode.O1,
        deployment=DeploymentSignals(),
        oracle=OracleSignals(failure_detected=True),
        attempts_used=4,
    ) == Decision.STOP_FAILURE


def test_o1_requires_oracle():
    with pytest.raises(ValueError):
        decide(
            mode=FeedbackMode.O1,
            deployment=DeploymentSignals(),
            attempts_used=1,
        )


def test_o1_uses_oracle_not_deployment_signals():
    assert decide(
        mode=FeedbackMode.O1,
        deployment=DeploymentSignals(
            parser_ok=False,
            planner_ok=False,
            pipeline_error=True,
        ),
        oracle=OracleSignals(failure_detected=False),
        attempts_used=1,
    ) == Decision.STOP_SUCCESS


def test_deployment_mode_ignores_oracle():
    assert decide(
        mode=FeedbackMode.DEPLOYMENT,
        deployment=DeploymentSignals(
            parser_ok=True,
            planner_ok=True,
        ),
        oracle=OracleSignals(failure_detected=True),
        attempts_used=1,
    ) == Decision.STOP_SUCCESS


def test_deployment_failure_refines():
    assert decide(
        mode=FeedbackMode.DEPLOYMENT,
        deployment=DeploymentSignals(
            parser_ok=False,
            planner_ok=False,
            pipeline_error=True,
        ),
        attempts_used=1,
    ) == Decision.REFINE


def test_deployment_failure_on_attempt_4_stops_failure():
    assert decide(
        mode=FeedbackMode.DEPLOYMENT,
        deployment=DeploymentSignals(
            parser_ok=False,
            planner_ok=False,
            pipeline_error=True,
        ),
        attempts_used=4,
    ) == Decision.STOP_FAILURE


def test_deployment_success_stops():
    assert decide(
        mode=FeedbackMode.DEPLOYMENT,
        deployment=DeploymentSignals(
            parser_ok=True,
            planner_ok=True,
        ),
        attempts_used=1,
    ) == Decision.STOP_SUCCESS


def test_verifier_inconsistency_refines():
    assert decide(
        mode=FeedbackMode.DEPLOYMENT,
        deployment=DeploymentSignals(
            parser_ok=True,
            planner_ok=True,
            verifier_consistent=False,
        ),
        attempts_used=1,
    ) == Decision.REFINE


def test_verifier_consistency_stops():
    assert decide(
        mode=FeedbackMode.DEPLOYMENT,
        deployment=DeploymentSignals(
            parser_ok=True,
            planner_ok=True,
            verifier_consistent=True,
        ),
        attempts_used=1,
    ) == Decision.STOP_SUCCESS
