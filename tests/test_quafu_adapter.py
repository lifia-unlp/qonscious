from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv
from qiskit import QuantumCircuit

from qonscious.adapters.quafu_backend_adapter import QuafuBackendAdapter

QUAFU_SIMULATOR_NAME = "ScQ-Sim10"  # name of the Quafu simulator backend used for testing


@pytest.fixture
def token_based_fixture():
    """This is the fixture for tests requiring Quafu API token."""
    load_dotenv()
    quafu_token = os.getenv("QUAFU_API_TOKEN", "")
    adapter = QuafuBackendAdapter(api_token=quafu_token, backend_name=QUAFU_SIMULATOR_NAME)
    return {
        "adapter": adapter,
    }


@pytest.fixture
def circuits_fixture():
    """This is the fixture for tests requiring predefined circuits."""
    phi_plus = QuantumCircuit(2)
    phi_plus.h(0)
    phi_plus.cx(0, 1)
    phi_plus.measure_all()
    return {
        "phi_plus": phi_plus,
    }


@pytest.mark.quafu_apikey_required
def test_service_availability(token_based_fixture):
    assert token_based_fixture["adapter"] is not None


@pytest.mark.quafu_apikey_required
def test_basic_figures(token_based_fixture):
    assert token_based_fixture["adapter"].n_qubits == 10


@pytest.mark.quafu_apikey_required
def test_run_simulated(token_based_fixture, circuits_fixture):
    result = token_based_fixture["adapter"].run(circuits_fixture["phi_plus"], shots=1024)
    assert result["counts"] is not None
    assert sum(result["counts"].values()) == 1024
    assert "00" in result["counts"] and "11" in result["counts"]
