# grade_fom.py
from __future__ import annotations

import math
import random
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from qiskit import QuantumCircuit

from qonscious.foms.figure_of_merit import FigureOfMerit

if TYPE_CHECKING:
    from qonscious.adapters.backend_adapter import BackendAdapter
    from qonscious.results.result_types import ExperimentResult, FigureOfMeritResult

MIN_QUBITS = 2  # Grover does not make sense below 2 qubits (N<4) N>M>1

class GroverFigureOfMerit(FigureOfMerit):

    def __init__(
        self,
        num_targets: int,
        lambda_factor: float,
        mu_factor: float,
        num_qubits: int | None = None,
        targets_int: list[int] | None = None,
    ) -> None:
        self.num_targets = int(num_targets)
        self.lambda_factor = float(lambda_factor)
        self.mu_factor = float(mu_factor)
        self.num_qubits = None if num_qubits is None else int(num_qubits)
        self.targets_int = None if targets_int is None else list(targets_int)

    def evaluate(self, backend_adapter: BackendAdapter) -> FigureOfMeritResult:
        """"""
        search_space, target_bitstrings = self._make_search_space_and_targets(
            self.num_targets,
            self.num_qubits,
            self.targets_int
        )
        M = len(target_bitstrings)                                # Lenght of targets
        n = len(target_bitstrings[0]) if M > 0 else 1             # Effective Qbits e.g. "000" = 3
        N = len(search_space)                                     # Search space size
        R = self._optimal_rounds(N, M)                            # Optimal Grover iterations

        calc_shots = self.compute_required_shots()
        qc = self._build_grover_circuit(n, target_bitstrings, R)

        run_result: ExperimentResult = backend_adapter.run(qc, shots=calc_shots)
        # Score calculation
        counts = run_result.get("counts", {})
        properties: dict = self._compute_score(counts, target_bitstrings, calc_shots)

        #another plausibles properties to add could be:
        #properties: dict[str, Any] = {
        #    "num_qubits": n,
        #    "targets_count": M,
        #    "grover_iterations": R,
        #    "search_space_size": N,
        #    "target_states": target_bitstrings,
        #    "lambda_factor": self.lambda_factor,
        #    "mu_factor": self.mu_factor,
        #    "shots": calc_shots,
        #    **metrics  # properties: dict =.... should be renamed to metrics
        #}
        evaluation_result: FigureOfMeritResult = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "figure_of_merit": self.__class__.__name__,
            "properties": properties,
            "experiment_result": run_result,
        }
        return evaluation_result

    def compute_required_shots(self) -> int:
        return 2000# Future implementation could adapt this based on N, M, R, etc.

    def _optimal_rounds(self, N: int, M: int) -> int: #times the oracle+diffusion is applied
        R = math.floor((math.pi / 4) * math.sqrt(N/M))
        return max(0, R)

    def _make_search_space_and_targets(
        self,
        num_targets: int,
        num_qubits: int | None,
        targets_int: list[int] | None,
    ) -> tuple[list[int], list[str]]:

        # --- Elegir n (qubits) y N (tamaño del espacio) ---
        if num_qubits is not None:
            n = int(num_qubits)
            if n < MIN_QUBITS:
                raise ValueError(
                    f"GroverFoM: num_qubits={n} doesn't have any sense without entangelment"
                    f"Grover requieres at least {MIN_QUBITS} Qbits (N>=4)."
                )
        else:
            # Si no lo pasan, inferimos y forzamos mínimo 2
            if targets_int and len(targets_int) > 0:
                max_val = max(targets_int)
                # n para representar el mayor target (0 -> 1 bit), luego clamp a 2
                inferred = 1 if max_val == 0 else math.ceil(math.log2(max_val + 1))
            else:
                # fallback simple a partir de cuántos objetivos hay
                inferred = math.ceil(math.log2(max(num_targets, 1)))
            n = max(MIN_QUBITS, inferred)

        N = 2**n
        real_space = list(range(N))

        # --- Elegir objetivos (enteros) dentro del rango real ---
        if targets_int is None:
            if num_targets > len(real_space):
                raise ValueError(
                    f"Num of Targets: ({num_targets}) > Search Space Lenght ({len(real_space)})"
                )
            chosen = random.sample(real_space, k=num_targets)
        else:
            chosen = list(targets_int)
            for t in chosen:
                if not (0 <= t < N):
                    raise ValueError(f"target out of range: {t} ∉ [0,{N-1}]")

        # --- Formatear objetivos a bitstrings de ancho n ---
        targets_binary = [format(t, f"0{n}b") for t in chosen]
        search_space = real_space
        return search_space, targets_binary

    def _build_grover_circuit(self, n: int, targets: list[str], R: int) -> QuantumCircuit:

        def build_local_oracle(marked_list: list[str], num_qubits: int) -> QuantumCircuit:
            qc_oracle = QuantumCircuit(num_qubits, name="Oracle")
            tgt = num_qubits - 1
            for bitstr in marked_list:
                bits_le = list(reversed(bitstr))  # Little-endian
                zeros = [i for i, b in enumerate(bits_le) if b == "0"]

                # Envolver con X los ceros
                for i in zeros:
                    qc_oracle.x(i)

                # Aplicar MCZ
                if num_qubits > 1:
                    qc_oracle.h(tgt)
                    qc_oracle.mcx(list(range(num_qubits - 1)), tgt)
                    qc_oracle.h(tgt)
                else:
                    qc_oracle.z(tgt)

                # Deshacer X
                for i in zeros:
                    qc_oracle.x(i)
            return qc_oracle

        def build_local_diffusion(num_qubits: int) -> QuantumCircuit:
            qc_diff = QuantumCircuit(num_qubits, name="Diffusion")
            qc_diff.h(range(num_qubits))
            qc_diff.x(range(num_qubits))

            if num_qubits > 1:
                qc_diff.h(num_qubits - 1)
                qc_diff.mcx(list(range(num_qubits - 1)), num_qubits - 1)
                qc_diff.h(num_qubits - 1)
            else:
                qc_diff.z(0)
            qc_diff.x(range(num_qubits))
            qc_diff.h(range(num_qubits))
            return qc_diff

        qc = QuantumCircuit(n, n, name="Grover")
        qc.h(range(n))

        oracle_gate = build_local_oracle(targets, n)
        diffusion_gate = build_local_diffusion(n)

        # Aplicamos las iteraciones
        for _ in range(R):
            qc.compose(oracle_gate, qubits=range(n), inplace=True)
            qc.compose(diffusion_gate, qubits=range(n), inplace=True)

        qc.measure(range(n), range(n))
        return qc

    def _compute_score(
        self,
        counts: dict[str, int],
        targets: list[str],
        shots: int,
    ) -> dict:

        P = {s: c / shots for s, c in counts.items()}
        #takes the probabilities of target states
        P_T = sum(P.get(s, 0.0) for s in targets)
        P_N = 1.0 - P_T
        # Standard deviation of target probabilities
        M = len(targets)
        if M:
            p_list = [P.get(s, 0.0) for s in targets]
            p_bar = P_T / M
            sigma_T = (sum((p - p_bar) ** 2 for p in p_list) / M) ** 0.5
        else:
            sigma_T = 0.0

        raw = P_T - (self.lambda_factor * sigma_T) - (self.mu_factor * P_N)
        score = 0.0 if (self.mu_factor * P_N >= P_T) else max(0.0, raw)
        return {"score": score,
                "P_T": P_T,
                "sigma_T": sigma_T,
                "P_N": P_N,
            }
