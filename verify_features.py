"""
Verify the new evolution features:
1. Retroactive evolution (only once per event).
2. Multiple evolution paths (Equal odds available).
"""
import sys
import os
sys.path.append('models')
sys.path.append('src')

from Pokemon import Pokemon

def run_verification():
    print("=" * 60)
    print("VERIFYING EVOLUTION FEATURES")
    print("=" * 60)

    # 1. Test Retroactive Evolution Restriction
    print("\n[Test 1] Retroactive Evolution (Charmander Lvl 50)")
    print("-" * 60)
    charmander = Pokemon(4, level=50) # Charmander
    print(f"Created: {charmander}")
    
    can, ids = charmander.can_evolve()
    print(f"Can evolve? {can}")
    print(f"Evolution IDs: {ids}")
    
    if can:
        print(">> Evolving once (simulating game loop)...")
        # Simulating user choosing 'y'
        res = charmander.evolve(ids[0])
        print(f"✓ Evolved to: {res['new_name']}")
        print(f"Current State: {charmander}")
        
    print(">> Checking if it auto-evolves again immediately (it should NOT in this script)")
    # We consciously DO NOT call evolve() again to simulate the game loop ending
    # But we can check if it IS eligible for next time
    can_next, ids_next = charmander.can_evolve()
    print(f"Eligible for next evolution event? {can_next} (IDs: {ids_next})")
    if can_next:
        print("✓ System correctly identifies next evolution is pending for NEXT event.")
    else:
        print("X Something wrong, Charmeleon should be able to evolve.")

    # 2. Test Branching Evolution
    print("\n[Test 2] Branching Evolution (Gloom Lvl 40)")
    print("-" * 60)
    # Gloom is ID 44. Evolves to 45 (Vileplume) or 182 (Bellossom) at Lvl 36 (mapped level)
    gloom = Pokemon(44, level=40)
    print(f"Created: {gloom}")
    
    can_branch, ids_branch = gloom.can_evolve()
    print(f"Can evolve? {can_branch}")
    print(f"Evolution IDs: {ids_branch}")
    
    if len(ids_branch) > 1:
        print(f"✓ SUCCESS: Found {len(ids_branch)} multiple evolution paths!")
    else:
        print(f"X FAILURE: Expected multiple paths (45, 182), found {ids_branch}")
        
    # Check Eevee as well if available (ID 133)
    print("\n[Test 3] Eevee Check (ID 133, Level 30)")
    eevee = Pokemon(133, level=30)
    can_eevee, ids_eevee = eevee.can_evolve()
    print(f"Eevee Candidates: {ids_eevee}")

if __name__ == "__main__":
    run_verification()
