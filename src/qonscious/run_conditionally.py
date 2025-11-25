from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qonscious.actions.qonscious_action import QonsciousAction
    from qonscious.adapters.backend_adapter import BackendAdapter
    from qonscious.checks.merit_compliance_check import MeritComplianceCheck
    from qonscious.results.result_types import FigureOfMeritResult, QonsciousResult


def run_conditionally(
    backend_adapter: BackendAdapter,
    checks: Sequence[MeritComplianceCheck],
    on_pass: QonsciousAction,
    on_fail: QonsciousAction,
    **kwargs: Any,
) -> QonsciousResult:
    """
    Main entry point of the Qonscious framework.

    Evaluates a set of merit compliance checks on the given backend
    and executes the appropriate action depending on whether all
    checks pass or any check fails.

    Args:
        backend_adapter: Adapter to the quantum backend on which figures of merit
            are evaluated and circuits may be executed.
        checks: The merit compliance checks to perform on the backend.
        on_pass:  Action to execute if all checks succeed. Must implement
            `run(backend_adapter, fom_results, **kwargs)` and return an `ExperimentResult`
             or `None`.
        on_fail: Action to execute if any check fails. Same contract as `on_pass`.
        **kwargs: Additional keyword arguments forwarded to the checks and actions.

    Returns:
        QonsciousResult: A result object containing the list of figure-of-merit results
            and, if applicable, the experiment result produced by the action.
    """

    fom_results: list[FigureOfMeritResult] = []
    passed = True

    for check in checks:
        result = check.check(backend_adapter, **kwargs)
        fom_results.append(result["fom_result"])
        if not result["passed"]:
            passed = False

    if passed:
        run_result = on_pass.run(backend_adapter, fom_results, **kwargs)
    else:
        run_result = on_fail.run(backend_adapter, fom_results, **kwargs)

    return {
        "condition": "pass" if passed else "fail",
        "figures_of_merit_results": fom_results,
        "experiment_result": run_result,
    }
