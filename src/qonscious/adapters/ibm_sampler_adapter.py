from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from .backend_adapter import BackendAdapter

if TYPE_CHECKING:
    from qiskit import QuantumCircuit

    from qonscious.results.result_types import ExperimentResult


class IBMSamplerAdapter(BackendAdapter):
    """Adapter to use IBM Quantum SamplerV2 as a remote backend.
    We can also use this to adapt the FakeXX backends"""

    def __init__(self, backend):
        self.backend = backend

    @classmethod
    def least_busy_backend(cls, token) -> Self:
        """Simply provide your IBM Quantum token to get an adaptor on the least busy backend."""
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        return cls(service.least_busy(operational=True, simulator=False))

    @classmethod
    def backend_named(cls, name, token) -> Self:
        """Get an adapter on a named backend."""
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        return cls(service.backend(name=name))

    @classmethod
    def all_available_backends(
        cls,
        token,
        **kwargs,
    ) -> list[Self]:
        """Get a list of adapters to backends available for the account with the provided token."""
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        return [cls(backend) for backend in service.backends(**kwargs)]

    @cached_property
    def _backend_configuration(self):
        "QPU configuration obtained as indicated in https://quantum.cloud.ibm.com/docs/en/guides/get-qpu-information"
        "Cached after first call - maybe we should not cache it"
        "cache can be cleared with ```del obj._backend_configuration```"
        return self.backend.configuration()

    @cached_property
    def _backend_properties(self):
        "QPU dynamic information obtained as indicated in https://quantum.cloud.ibm.com/docs/en/guides/get-qpu-information"
        "Cached after first call - maybe we should not cache it"
        "cache can be cleared with ```del obj._backend_properties```"
        return self.backend.properties()

    @property
    def n_qubits(self) -> int:
        return self._backend_configuration.n_qubits

    @property
    def t1s(self) -> dict[int, float]:
        n_qubits = self._backend_configuration.n_qubits
        return {i: self._backend_properties.t1(i) for i in range(n_qubits)}

    @property
    def t2s(self) -> dict[int, float]:
        n_qubits = self._backend_configuration.n_qubits
        return {i: self._backend_properties.t2(i) for i in range(n_qubits)}

    @property
    def name(self) -> str:
        return self.backend.name

    def run(self, circuit: QuantumCircuit, **kwargs) -> ExperimentResult:
        kwargs.setdefault("shots", 1024)
        sampler = Sampler(mode=self.backend)
        transpiled_circuit = transpile(circuit, self.backend, optimization_level=3)
        job = sampler.run([transpiled_circuit], **kwargs)
        result = job.result()
        timestamps = job.metrics().get("timestamps", {})
        counts = _extract_counts(result)
        return {
            "counts": counts,
            "shots": kwargs["shots"],
            "backend_properties": {"name": self.backend.name},
            "timestamps": timestamps,
            "raw_results": result,
        }


def _extract_counts(result) -> dict:
    data = result[0].data
    field_names = [
        k for k in dir(data) if not k.startswith("_") and hasattr(getattr(data, k), "get_counts")
    ]
    if len(field_names) != 1:
        raise ValueError(f"Expected exactly one data field with get_counts(), got: {field_names}")
    return getattr(data, field_names[0]).get_counts()
