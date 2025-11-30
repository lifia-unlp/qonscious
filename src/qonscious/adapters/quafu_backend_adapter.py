from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qiskit import QuantumCircuit
    from quafu.backends.backends import Backend as QuafuBackend

    from qonscious.results.result_types import ExperimentResult

from quafu import QuantumCircuit as QuafuQuantumCircuit, Task, User

from qonscious.adapters.backend_adapter import BackendAdapter


class QuafuBackendAdapter(BackendAdapter):
    """Adapter for Quafu with interactive backend selection during CHSH tests."""

    def __init__(self, backend_name: str, api_token: str):
        self.user = User(api_token)
        self.backend = self._get_backend(backend_name)

    def _get_backend(self, backend_name: str) -> QuafuBackend:
        backends = self.user.get_available_backends()
        return backends[backend_name]

    def run(self, circuit: QuantumCircuit, **kwargs) -> ExperimentResult:
        shots = kwargs.get("shots", 1024)

        # Convert Qiskit circuit to Quafu circuit
        quafu_circuit = self._convert_circuit(circuit)

        try:
            task = Task(self.user)
            task.config(backend=self.backend.name, shots=shots, compile=True)

            # Submit task
            submit_result = task.send(quafu_circuit, wait=False)
            task_id = submit_result.taskid

            # Wait for completion
            max_wait_time = 300  # 5 minutes maximum
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                try:
                    # Get task status
                    task_status = task.retrieve(task_id)

                    # Check status attribute
                    status = None
                    if hasattr(task_status, "status"):
                        status = task_status.status
                    elif hasattr(task_status, "task_status"):
                        status = task_status.task_status
                    elif hasattr(task_status, "state"):
                        status = task_status.state

                    if status == "Completed":
                        print(" ✅")
                        break
                    elif status in ["Failed", "Cancelled", "Error"]:
                        print(f"\n❌ Task failed: {status}")
                        break

                    print(".", end="", flush=True)
                    time.sleep(5)

                except Exception as e:
                    print(f"\n⚠️  Error checking status: {e}")
                    time.sleep(5)
                    continue
            else:
                print("\n⏰ Timeout waiting for results")

            # Get results
            counts = {}
            if hasattr(task_status, "results") and hasattr(task_status.results, "counts"):
                counts = task_status.results.counts
            elif hasattr(task_status, "counts"):
                counts = task_status.counts
            elif hasattr(submit_result, "counts"):
                counts = submit_result.counts

            # 🔥 CRITICAL FIX: Convert Quafu (little-endian) to expected format (big-endian)
            converted_counts = {}
            for bitstring, count in counts.items():
                # Quafu returns little-endian, CHSH function expects big-endian format
                converted_bitstring = bitstring[::-1]  # Reverse the bit order
                converted_counts[converted_bitstring] = count

            print(f"🔀 Endianness conversion: {len(counts)} counts converted")
            if counts:
                example_orig = list(counts.keys())[0]
                example_conv = list(converted_counts.keys())[0]
                print(f"🔀 Example: '{example_orig}' -> '{example_conv}'")

            return {
                "counts": converted_counts,  # 🔥 Use converted counts
                "shots": shots,
                "backend_properties": {
                    "name": f"quafu_{self.backend.name}",
                    "task_id": task_id,
                },
                "timestamps": {
                    "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
                "raw_results": task_status,
            }

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()
            return {
                "counts": {},
                "shots": shots,
                "backend_properties": {
                    "name": f"quafu_{self.backend_name}",
                    "error": str(e),
                    "token_used": self._token_provided,
                },
                "timestamps": {"created": "", "finished": ""},
                "raw_results": None,
            }

    def _simplify_angles(self, params):
        """Convert angles to exact fractions of pi for better precision."""
        simplified = []
        for angle in params:
            # Identificar ángulos comunes con tolerancia
            if abs(angle - 0.7853981633974483) < 1e-10:  # π/4
                simplified_angle = math.pi / 4
                simplified.append(simplified_angle)
            elif abs(angle - 1.5707963267948966) < 1e-10:  # π/2
                simplified_angle = math.pi / 2
                simplified.append(simplified_angle)
            elif abs(angle + 0.7853981633974483) < 1e-10:  # -π/4
                simplified_angle = -math.pi / 4
                simplified.append(simplified_angle)
            elif abs(angle + 1.5707963267948966) < 1e-10:  # -π/2
                simplified_angle = -math.pi / 2
                simplified.append(simplified_angle)
            elif abs(angle - 3.141592653589793) < 1e-10:  # π
                simplified_angle = math.pi
                simplified.append(simplified_angle)
            elif abs(angle + 3.141592653589793) < 1e-10:  # -π
                simplified_angle = -math.pi
                simplified.append(simplified_angle)
            else:
                simplified.append(angle)
        return simplified

    def _convert_circuit(self, qiskit_circuit: QuantumCircuit) -> QuafuQuantumCircuit:
        """Convert Qiskit circuit to Quafu circuit usando OpenQASM 2.0"""

        try:
            # 🔥 NUEVO: Convertir a OpenQASM 2.0
            qasm_str = qiskit_circuit.qasm()
            print(f"🔧 OpenQASM conversion: {len(qasm_str)} characters")

            # Crear circuito Quafu desde OpenQASM
            quafu_circuit = QuafuQuantumCircuit(qiskit_circuit.num_qubits)
            quafu_circuit.from_openqasm(qasm_str)

            print("✅ Circuito convertido via OpenQASM")
            print(f"✅ Instrucciones Quafu: {len(quafu_circuit.instructions)}")

            # Mostrar algunas instrucciones para debug
            print("\n📋 PRIMERAS 10 INSTRUCCIONES QUAFU:")
            for i, gate in enumerate(quafu_circuit.instructions[:10]):
                print(f"  {i:2d}. {gate}")
            if len(quafu_circuit.instructions) > 10:
                print(f"  ... y {len(quafu_circuit.instructions) - 10} más")

            return quafu_circuit

        except Exception as e:
            print(f"⚠️  OpenQASM conversion failed: {e}")
            print("🔄 Fallback a conversión manual...")
            return self._convert_circuit_manual(qiskit_circuit)

    def _convert_circuit_manual(self, qiskit_circuit: QuantumCircuit) -> QuafuQuantumCircuit:
        """Fallback: conversión manual de circuito"""
        quafu_circuit = QuafuQuantumCircuit(qiskit_circuit.num_qubits)

        print(f"🔧 Converting circuit manually: {len(qiskit_circuit)} instructions")
        print(f"🔧 Qiskit circuit qubits: {qiskit_circuit.num_qubits}")

        # Debug: show all Qiskit circuit instructions
        print("\n📋 QISKIT INSTRUCTIONS:")
        for i, instruction in enumerate(qiskit_circuit):
            gate_name = instruction.operation.name
            qubits = (
                [q.index for q in instruction.qubits]
                if hasattr(instruction.qubits[0], "index")
                else [q._index for q in instruction.qubits]
            )
            params = getattr(instruction.operation, "params", [])
            print(f"  {i:2d}. {gate_name:8} qubits{qubits} params{params}")

        converted_count = 0
        print("\n🎯 PRECISION CONVERSION:")
        for i, instruction in enumerate(qiskit_circuit):
            try:
                gate_name = instruction.operation.name

                # Extract qubit indices
                qubit_indices = []
                for q in instruction.qubits:
                    if hasattr(q, "index"):
                        qubit_indices.append(q.index)
                    elif hasattr(q, "_index"):
                        qubit_indices.append(q._index)
                    else:
                        qubit_indices.append(instruction.qubits.index(q))

                # PARAMETERS WITH IMPROVED PRECISION
                params = []
                if hasattr(instruction.operation, "params"):
                    original_params = [float(p) for p in instruction.operation.params]
                    if original_params and gate_name in ["rx", "ry", "rz"]:
                        print(f"  Gate {i}: {gate_name} on {qubit_indices}")
                        params = self._simplify_angles(original_params)
                    else:
                        params = original_params

                # GATE CONVERSION
                converted = False
                if gate_name == "h" and len(qubit_indices) == 1:
                    quafu_circuit.h(qubit_indices[0])
                    converted = True
                elif gate_name == "x" and len(qubit_indices) == 1:
                    quafu_circuit.x(qubit_indices[0])
                    converted = True
                elif gate_name == "y" and len(qubit_indices) == 1:
                    quafu_circuit.y(qubit_indices[0])
                    converted = True
                elif gate_name == "z" and len(qubit_indices) == 1:
                    quafu_circuit.z(qubit_indices[0])
                    converted = True
                elif gate_name == "rx" and len(qubit_indices) == 1 and params:
                    quafu_circuit.rx(qubit_indices[0], params[0])
                    converted = True
                elif gate_name == "ry" and len(qubit_indices) == 1 and params:
                    quafu_circuit.ry(qubit_indices[0], params[0])
                    converted = True
                elif gate_name == "rz" and len(qubit_indices) == 1 and params:
                    quafu_circuit.rz(qubit_indices[0], params[0])
                    converted = True
                elif gate_name == "cx" and len(qubit_indices) == 2:
                    quafu_circuit.cnot(qubit_indices[0], qubit_indices[1])
                    converted = True
                elif gate_name == "ccx" and len(qubit_indices) == 3:
                    # Para CCX, usar descomposición básica
                    print(f"  🔄 CCX {qubit_indices} → descomposición básica")
                    self._add_ccx_decomposition(
                        quafu_circuit, qubit_indices[0], qubit_indices[1], qubit_indices[2]
                    )
                    converted = True
                elif gate_name == "measure":
                    converted = True  # Handled at the end
                    pass

                if converted:
                    converted_count += 1
                else:
                    print(f"⚠️  Gate {i}: {gate_name}{params} on {qubit_indices} - not supported")

            except Exception as e:
                print(f"❌ Error in instruction {i}: {e}")
                continue

        quafu_circuit.measure(list(range(qiskit_circuit.num_qubits)))
        print(f"✅ Circuit converted: {converted_count}/{len(qiskit_circuit)} instructions")
        print(f"✅ Final Quafu instructions: {len(quafu_circuit.instructions)}")

        return quafu_circuit

    def _add_ccx_decomposition(self, circuit, control1, control2, target):
        """Descomposición básica de CCX como fallback"""
        # Implementación simple usando CNOTs y Hadamards
        circuit.h(target)
        circuit.cnot(control2, target)
        circuit.tdg(target)
        circuit.cnot(control1, target)
        circuit.t(target)
        circuit.cnot(control2, target)
        circuit.tdg(target)
        circuit.cnot(control1, target)
        circuit.t(control2)
        circuit.t(target)
        circuit.h(target)
        circuit.cnot(control1, control2)
        circuit.t(control1)
        circuit.tdg(control2)
        circuit.cnot(control1, control2)

    @property
    def n_qubits(self) -> int:
        return self.backend.qubit_num

    @property
    def t1s(self) -> dict[int, float] | None:
        return None

    @property
    def t2s(self) -> dict[int, float] | None:
        return None

    @property
    def name(self) -> str:
        return self.backend.name
