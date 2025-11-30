# qonscious/foms/packed_tilted_chsh.py
import numpy as np
from datetime import datetime, timezone
from qiskit import QuantumCircuit
from qonscious.foms.figure_of_merit import FigureOfMerit


class PackedTiltedCHSHTest(FigureOfMerit):
    """
    Tilted (inclinado) CHSH test optimizado para detectores/readout imperfectos.
    Usa el estado y mediciones óptimas del paper Nature npj Quantum Inf. (2025)
    https://www.nature.com/articles/s41534-025-01029-6
    """



    def __init__(self, eta: float = 1.0):
    """
    eta: eficiencia de detección o fidelidad promedio de readout (ej: 0.90 para 90%)
    Se asume simétrica en ambos lados.
    """
    
    
        if not 0.66 < eta <= 1.0:
            raise ValueError("eta debe estar entre ~0.67 y 1.0 para tener ventaja cuántica")
        self.eta = float(eta)
        self.alpha = 0.0 if eta >= 1.0 else (1.0 / eta - 1.0)
        
        # Parámetros óptimos para tilted CHSH
        self.beta = np.pi/4 if self.alpha == 0 else np.arctan(np.sqrt(self.alpha))
        
    def _max_quantum_value(self) -> float:
        return 2.0 * np.sqrt(2.0 * (1.0 + self.alpha))

    def _build_bell_state(self) -> QuantumCircuit:
        qc = QuantumCircuit(2, 2)
        qc.ry(2 * self.beta, 0)
        qc.cx(0, 1)
        return qc

    def _build_measurement_circuit(self, alice_setting: int, bob_setting: int) -> QuantumCircuit:
        qc = self._build_bell_state()
        
        # Alice: A0=Z, A1=X
        if alice_setting == 1:
            qc.h(0)
        
        # Bob: B0 a -45°, B1 a +45°
        if bob_setting == 0:
            qc.ry(-np.pi/4, 1)
        else:
            qc.ry(+np.pi/4, 1)
        
        qc.measure([0, 1], [0, 1])
        return qc

    def _compute_expectation(self, counts: dict) -> float:
        total = sum(counts.values())
        if total == 0:
            return 0.0
        
        corr = 0
        for outcome, count in counts.items():
            if len(outcome) >= 2:
                a, b = int(outcome[0]), int(outcome[1])
                corr += (1 if a == b else -1) * count
        
        return corr / total

    def _compute_single_expectation(self, counts: dict) -> float:
        total = sum(counts.values())
        if total == 0:
            return 0.0
        
        exp = 0
        for outcome, count in counts.items():
            if len(outcome) >= 1:
                bit = int(outcome[0])
                exp += (1 if bit == 0 else -1) * count
        
        return exp / total

    def evaluate(self, backend_adapter, **kwargs):
        shots = kwargs.get("shots", 100000)
        
        expectations = {}
        for a in [0, 1]:
            for b in [0, 1]:
                circuit = self._build_measurement_circuit(a, b)
                result = backend_adapter.run(circuit, shots=shots)
                expectations[f"A{a}B{b}"] = self._compute_expectation(result["counts"])

        # Medir ⟨A1⟩
        circuit_A1 = QuantumCircuit(2, 1)
        circuit_A1.ry(2 * self.beta, 0)
        circuit_A1.cx(0, 1)
        circuit_A1.h(0)
        circuit_A1.measure(0, 0)
        result_A1 = backend_adapter.run(circuit_A1, shots=shots)
        A1_exp = self._compute_single_expectation(result_A1["counts"])

        # Calcular score
        A0B0, A0B1, A1B0, A1B1 = (expectations[k] for k in ["A0B0", "A0B1", "A1B0", "A1B1"])
        chsh_raw = A0B0 + A0B1 + A1B0 - A1B1
        tilted_score = chsh_raw + self.alpha * A1_exp

        return {
            "figure_of_merit": "PackedTiltedCHSHTest",
            "properties": {
                "score": tilted_score,
                "raw_CHSH": chsh_raw,
                "alpha": self.alpha,
                "eta": self.eta,
                "A1_expectation": A1_exp,
                "expectations": expectations,
                "max_quantum_bound": self._max_quantum_value(),
                "quantum_efficiency": tilted_score / self._max_quantum_value(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
