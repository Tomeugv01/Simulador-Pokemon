"""
Quick test to verify evolution system still works after removing evolves_to_id
"""
import sys
sys.path.insert(0, 'models')
sys.path.insert(0, 'src')

from Pokemon import Pokemon

# Test 1: Charmander at level 16 (should be able to evolve)
print("="*60)
print("TEST 1: Charmander at Level 16 (Standard Evolution)")
print("="*60)
charmander = Pokemon(4, level=16)  # Charmander ID 4
print(f"Pokemon: {charmander.name} (ID: {charmander.id})")
print(f"Level: {charmander.level}")
print(f"Evolution Level: {charmander.evolution_level}")

can_evolve, evo_ids = charmander.can_evolve()
print(f"\nCan Evolve: {can_evolve}")
print(f"Evolution Target IDs: {evo_ids}")

if can_evolve:
    print(f"✓ Evolution check works! Can evolve to Pokemon ID {evo_ids[0]}")
else:
    print("✗ FAILED - Should be able to evolve")

# Test 2: Charmander at level 50 (retroactive evolution)
print("\n" + "="*60)
print("TEST 2: Charmander at Level 50 (Retroactive Evolution)")
print("="*60)
charmander2 = Pokemon(4, level=50)
print(f"Pokemon: {charmander2.name} (ID: {charmander2.id})")
print(f"Level: {charmander2.level}")

can_evolve2, evo_ids2 = charmander2.can_evolve()
print(f"\nCan Evolve: {can_evolve2}")
print(f"Evolution Target IDs: {evo_ids2}")

if can_evolve2:
    print(f"✓ Retroactive evolution works! Can evolve to Pokemon ID {evo_ids2[0]}")
else:
    print("✗ FAILED - Should be able to evolve")

# Test 3: Squirtle at level 10 (cannot evolve yet)
print("\n" + "="*60)
print("TEST 3: Squirtle at Level 10 (Too Low to Evolve)")
print("="*60)
squirtle = Pokemon(7, level=10)
print(f"Pokemon: {squirtle.name} (ID: {squirtle.id})")
print(f"Level: {squirtle.level}")
print(f"Evolution Level: {squirtle.evolution_level}")

can_evolve3, evo_ids3 = squirtle.can_evolve()
print(f"\nCan Evolve: {can_evolve3}")
print(f"Evolution Target IDs: {evo_ids3}")

if not can_evolve3:
    print("✓ Correctly prevents premature evolution")
else:
    print("✗ FAILED - Should NOT be able to evolve yet")

# Test 4: Check if Eevee has multiple evolution paths
print("\n" + "="*60)
print("TEST 4: Eevee Multiple Evolution Paths")
print("="*60)
eevee = Pokemon(133, level=20)  # Eevee ID 133
print(f"Pokemon: {eevee.name} (ID: {eevee.id})")
print(f"Level: {eevee.level}")

can_evolve4, evo_ids4 = eevee.can_evolve()
print(f"\nCan Evolve: {can_evolve4}")
print(f"Evolution Target IDs: {evo_ids4}")

if can_evolve4 and len(evo_ids4) > 1:
    print(f"✓ Multiple evolution paths detected: {len(evo_ids4)} options")
elif can_evolve4:
    print(f"⚠ Evolution works but only {len(evo_ids4)} path(s) found")
else:
    print("Note: Eevee evolution might require special items/conditions")

print("\n" + "="*60)
print("EVOLUTION SYSTEM TEST COMPLETE")
print("="*60)
