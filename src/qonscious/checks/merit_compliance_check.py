from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable

    from qonscious.adapters.backend_adapter import BackendAdapter
    from qonscious.foms.figure_of_merit import FigureOfMerit
    from qonscious.results.result_types import FigureOfMeritResult


class MeritComplianceCheck:
    """
    A flexible compliance check based on an optional Figure of Merit
    and a custom decision function that maps its result to a boolean.
    """

    def __init__(
        self,
        figure_of_merit: FigureOfMerit,
        decision_function: Callable[[FigureOfMeritResult], bool] = lambda _: True,
    ):
        self.figure_of_merit = figure_of_merit
        self.decision_function = decision_function

    def check(self, backend_adapter: BackendAdapter, **kwargs) -> dict:
        """
        Evaluate the FOM if present, apply the decision function to its result,
        and return a dict with the compliance outcome and the FOM result (if any).
        """

        fom_result = self.figure_of_merit.evaluate(backend_adapter, **kwargs)

        passed = self.decision_function(fom_result)

        return {"passed": passed, "fom_result": fom_result}
