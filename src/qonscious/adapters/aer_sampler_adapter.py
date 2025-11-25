from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import psutil
from qiskit.primitives.containers import BitArray
from qiskit_aer.primitives import SamplerV2 as Sampler

from .backend_adapter import BackendAdapter

if TYPE_CHECKING:
    from qiskit import QuantumCircuit

    from qonscious.results.result_types import ExperimentResult


class AerSamplerAdapter(BackendAdapter):
    """Adapter to use Qiskit Aer SamplerV2 as a local backend.
    Under the hood it will use an AerSimulator, but we do not care about it;
    we let Aer choose how to do that. If we care about controlling the Simulator,
    we better use AerSimulatorAdapter instead."""

    def __init__(self, sampler: Sampler | None = None):
        self.sampler = sampler or Sampler()

    @property
    def n_qubits(self) -> int:
        "Estimates the maximum number of qubits this computer can simulate"
        "considering the available memory and some rules of thumb"
        return int(math.log2(psutil.virtual_memory().available / 16))

    @property
    def t1s(self) -> dict[int, float]:
        "In an aer simulator, there is no limit on the t1."
        "It could be different if we include a noise model"
        return {qubit: float("inf") for qubit in range(self.n_qubits)}

    @property
    def t2s(self) -> dict[int, float]:
        "In an aer simulator, there is no limit on the t2."
        "It could be different if we include a noise model"
        return {qubit: float("inf") for qubit in range(self.n_qubits)}

    @property
    def name(self) -> str:
        return "SamplerV2"

    def run(self, circuit: QuantumCircuit, **kwargs) -> ExperimentResult:
        shots = kwargs.get("shots", 1024)
        created = datetime.now(timezone.utc).isoformat()
        job = self.sampler.run(pubs=[circuit], shots=shots)
        running = datetime.now(timezone.utc).isoformat()
        result = job.result()[0]
        finished = datetime.now(timezone.utc).isoformat()

        raw = result.join_data()
        arr = raw.astype("uint8", copy=False) if not isinstance(raw, BitArray) else raw.array
        counts = BitArray(arr, circuit.num_clbits).get_counts()

        return {
            "counts": counts,
            "shots": shots,
            "backend_properties": {"name": "qiskit_aer.primitives.SamplerV2"},
            "timestamps": {
                "created": created,
                "running": running,
                "finished": finished,
            },
            "raw_results": job.result(),
        }
