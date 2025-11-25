from __future__ import annotations

import os
import statistics
from typing import TYPE_CHECKING

import pytest
from pytest import approx
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService

from qonscious.adapters.aer_simulator_adapter import AerSimulatorAdapter

if TYPE_CHECKING:
    from qonscious.results.result_types import ExperimentResult

TEST_BACKEND_NAME = "ibm_torino"


@pytest.mark.ibm_token_required
def test_aer_sampler_basic_run():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    ibm_token = os.getenv("IBM_QUANTUM_TOKEN")
    adapter = AerSimulatorAdapter.based_on(token=ibm_token, backend_name=TEST_BACKEND_NAME)
    result: ExperimentResult = adapter.run(qc, shots=1024)

    # Check result is a dict with expected keys
    assert isinstance(result, dict)
    assert set(result.keys()) >= {
        "counts",
        "shots",
        "timestamps",
        "raw_results",
        "backend_properties",
    }

    # Validate counts format
    counts = result["counts"]
    assert isinstance(counts, dict)
    assert all(isinstance(k, str) and len(k) == 2 for k in counts)
    assert all(isinstance(v, int) and v >= 0 for v in counts.values())
    assert sum(counts.values()) == 1024

    # Validate backend name
    assert result["backend_properties"]["name"] == "qiskit_aer.primitives.SamplerV2"

    # Validate timestamps
    timestamps = result["timestamps"]
    assert isinstance(timestamps, dict)
    assert all(k in timestamps for k in ("created", "running", "finished"))
    assert all(isinstance(timestamps[k], str) for k in timestamps)


@pytest.mark.ibm_token_required
def test_props():
    ibm_token = os.getenv("IBM_QUANTUM_TOKEN")

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=ibm_token)
    backend_to_compare_to = service.backend(TEST_BACKEND_NAME)
    adapter = AerSimulatorAdapter.based_on(token=ibm_token, backend_name=TEST_BACKEND_NAME)
    n_qubits = adapter.n_qubits
    assert n_qubits == backend_to_compare_to.configuration().n_qubits
    t1s_avg = sum(adapter.t1s.values()) / len(adapter.t1s)
    t2s_avg = sum(adapter.t2s.values()) / len(adapter.t2s)
    qubit_props = [
        backend_to_compare_to.properties().qubit_property(i)
        for i in range(backend_to_compare_to.configuration().n_qubits)
    ]
    real_t1_avg = statistics.mean(
        [props["T1"][0] for props in qubit_props if props["T1"][0] is not None]
    )
    real_t2_avg = statistics.mean(
        [props["T2"][0] for props in qubit_props if props["T2"][0] is not None]
    )
    assert t1s_avg == approx(real_t1_avg, rel=1e-9, abs=1e-12)
    assert t2s_avg == approx(real_t2_avg, rel=1e-9, abs=1e-12)
