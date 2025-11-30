import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Ahora puedes importar qonscious
from qonscious import run_conditionally
from qonscious.actions import QonsciousCallable
from qonscious.adapters import QuafuBackendAdapter
from qonscious.checks import MeritComplianceCheck
from qonscious.foms import PackedCHSHTest


def test_quafu_interactive():
    """Prueba el adapter de Quafu con selección interactiva"""

    print("🧪 TEST QUAFU INTERACTIVO LOCAL")
    print("=" * 50)

    try:
        # Crear adapter sin backend - se seleccionará interactivamente
        print("🔄 Creando adapter Quafu...")
        adapter = QuafuBackendAdapter()

        # Configurar check CHSH
        chsh_check = MeritComplianceCheck(
            figure_of_merit=PackedCHSHTest(),
            decision_function=lambda result: (
                result is not None and
                result["properties"]["score"] > 2.0
            )
        )

        # Acciones simples
        def pass_action(backend, fom_results, **kwargs):
            score = fom_results[0]["properties"]["score"]
            print(f"✅ CHSH PASÓ - Score: {score:.3f}")
            return {"resultado": "cuántico", "score": score}

        def fail_action(backend, fom_results, **kwargs):
            score = fom_results[0]["properties"]["score"]
            print(f"❌ CHSH FALLÓ - Score: {score:.3f}")
            return {"resultado": "clásico", "score": score}

        print("\n🎯 EJECUTANDO RUN_CONDITIONALLY...")
        print("   Esto activará la selección interactiva de backend Quafu")

        # Esto activará la selección interactiva cuando CHSH ejecute su circuito de 8 qubits
        result = run_conditionally(
            backend_adapter=adapter,
            checks=[chsh_check],
            on_pass=QonsciousCallable(pass_action),
            on_fail=QonsciousCallable(fail_action),
            shots=1024
        )

        # Mostrar resultados
        print("\n" + "=" * 50)
        print("📊 RESULTADOS FINALES:")
        print(f"   Backend usado: {adapter.name}")
        print(f"   Condición: {result['condition']}")

        if result['figures_of_merit_results']:
            score = result['figures_of_merit_results'][0]["properties"]["score"]
            print(f"   CHSH Score: {score:.3f}")

        if result['experiment_result']:
            print(f"   Acción ejecutada: {result['experiment_result']}")

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_quafu_interactive()
