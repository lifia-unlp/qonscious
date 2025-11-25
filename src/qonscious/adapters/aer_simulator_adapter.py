from __future__ import annotations

from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService

from .backend_adapter import BackendAdapter

if TYPE_CHECKING:
    from qiskit_aer.backends.backendconfiguration import AerBackendConfiguration
    from qiskit_aer.backends.backendproperties import AerBackendProperties

    from qonscious.results.result_types import ExperimentResult


class AerSimulatorAdapter(BackendAdapter):
    """Adapter to use Qiskit AerSimulator as a local backend.
    We can simulate a specific IBM Quantum backend by passing a token and the backend name.
    The adapter will retrieve the noise model from IBM Quantum and configure the AerSimulator.
    Future versions will let you pass a hand-made noise model as well.
    Future version will be better suited to simulate non-IBM backends as well.
    """

    def __init__(self, simulator: AerSimulator, qubits_properties: list, backend_name: str):
        self.simulator = simulator or AerSimulator()
        self.qubits_properties = qubits_properties
        self.backend_name = backend_name

    @classmethod
    def based_on(cls, token, backend_name) -> Self:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        backend_to_simulate = service.backend(backend_name)
        return cls(
            AerSimulator.from_backend(backend_to_simulate),
            [
                backend_to_simulate.properties().qubit_property(i)
                for i in range(backend_to_simulate.configuration().n_qubits)
            ],
            backend_name,
        )

    def transpile(self, circuit: QuantumCircuit) -> QuantumCircuit:
        return transpile(circuit, self.simulator, optimization_level=3)

    @cached_property
    def _backend_properties(self) -> AerBackendProperties | None:
        return self.simulator.properties()

    @cached_property
    def _backend_configuration(self) -> AerBackendConfiguration:
        return self.simulator.configuration()

    @property
    def n_qubits(self) -> int:
        return self._backend_configuration.n_qubits

    @property
    def t1s(self) -> dict[int, float]:
        return {i: self.qubits_properties[i]["T1"][0] for i in range(len(self.qubits_properties))}

    @property
    def t2s(self) -> dict[int, float]:
        return {i: self.qubits_properties[i]["T2"][0] for i in range(len(self.qubits_properties))}

    @property
    def name(self) -> str:
        return self.backend_name

    def run(self, circuit: QuantumCircuit, **kwargs) -> ExperimentResult:
        shots = kwargs.get("shots", 1024)
        created = datetime.now(timezone.utc).isoformat()
        transpiled_circuit = self.transpile(circuit)
        job = self.simulator.run(transpiled_circuit, shots=shots)
        running = datetime.now(timezone.utc).isoformat()
        result = job.result()
        finished = datetime.now(timezone.utc).isoformat()

        counts = result.get_counts(transpiled_circuit)

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
