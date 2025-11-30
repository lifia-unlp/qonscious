# test_packed_tilted_chsh.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from qonscious.adapters.aer_sampler_adapter import AerSamplerAdapter
from qonscious.foms.packed_tilted_chsh import PackedTiltedCHSHTest
import numpy as np

def test_ideal():
    backend = AerSamplerAdapter()
    
    test_cases = [
        (1.0, "CHSH estándar"),
        (0.9, "Buena eficiencia"), 
        (0.8, "Eficiencia realista"),
        (0.7071, "Límite teórico"),
        (0.67, "Justo por encima del límite")
    ]
    
    print("=" * 60)
    
    for eta, description in test_cases:
        print(f"\nTEST: {description} → η = {eta:.4f}")
        print("=" * 60)
        
        try:
            fom = PackedTiltedCHSHTest(eta=eta)
            result = fom.evaluate(backend, shots=32768)
            r = result["properties"]
            
            score = r['score']
            bound = r['max_quantum_bound']
            
            print(f"\nSCORE OBTENIDO : {score:.6f}")
            print(f"LÍMITE CUÁNTICO: {bound:.6f}")
            
            # Verificar que estamos en el régimen cuántico
            if score > 2.0:  # Límite clásico
                print("✓ VIOLACIÓN DEL LÍMITE CLÁSICO DETECTADA!")
            else:
                print("Advertencia: Aún hay margen de mejora")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Algunos casos necesitan más shots o ajustes menores")
    print("=" * 60)

if __name__ == "__main__":
    test_ideal()
