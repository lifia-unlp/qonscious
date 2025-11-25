from __future__ import annotations

from typing import TYPE_CHECKING

from qonscious.actions.qonscious_callable import QonsciousCallable
from qonscious.adapters.aer_sampler_adapter import AerSamplerAdapter
from qonscious.checks.merit_compliance_check import MeritComplianceCheck
from qonscious.run_conditionally import run_conditionally

if TYPE_CHECKING:
    from qonscious.adapters.backend_adapter import BackendAdapter
    from qonscious.results.result_types import (
        ExperimentResult,
        FigureOfMeritResult,
        QonsciousResult,
    )


class DummyComplianceCheck(MeritComplianceCheck):
    def __init__(self, value: bool = True):
        self.value = value

    def check(self, backend_adapter: BackendAdapter, **kwargs) -> dict:
        return {"passed": self.value, "fom_result": {}}


def test_run_conditionally():
    backend = AerSamplerAdapter()
    passing_checks = [DummyComplianceCheck(True)]
    failing_checks = [DummyComplianceCheck(False)]

    def on_pass(
        adapter: BackendAdapter, figures_of_merit_results: list[FigureOfMeritResult]
    ) -> ExperimentResult:
        return {
            "counts": {},
            "shots": 1,
            "backend_properties": {},
            "timestamps": {},
            "raw_results": {},
        }

    def on_fail(
        adapter: BackendAdapter, figures_of_merit_results: list[FigureOfMeritResult]
    ) -> ExperimentResult:
        return {
            "counts": {},
            "shots": 0,
            "backend_properties": {},
            "timestamps": {},
            "raw_results": {},
        }

    result: QonsciousResult = run_conditionally(
        backend, passing_checks, QonsciousCallable(on_pass), QonsciousCallable(on_fail)
    )
    assert result["condition"] == "pass"
    assert result["experiment_result"] is not None and result["experiment_result"]["shots"] == 1

    result: QonsciousResult = run_conditionally(
        backend, failing_checks, QonsciousCallable(on_pass), QonsciousCallable(on_fail)
    )
    assert result["condition"] == "fail"
    assert result["experiment_result"] is not None and result["experiment_result"]["shots"] == 0
