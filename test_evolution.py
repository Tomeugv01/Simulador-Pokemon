"""
Test the new evolution system
"""
import sys
sys.path.append('models')
sys.path.append('src')

from Pokemon import Pokemon

print("=" * 60)
print("TESTING NEW EVOLUTION SYSTEM")
print("=" * 60)

# Test 1: Create a Charmander at level 15 (just below evolution)
print("\nTest 1: Charmander at level 15 (below evolution threshold)")
print("-" * 60)
charmander = Pokemon(4, level=15)
can_evolve, evo_ids = charmander.can_evolve()
print(f"{charmander.name} (Level {charmander.level})")
print(f"Evolution level: {charmander.evolution_level}")
print(f"Evolves to ID: {charmander.evolves_to_id}")
print(f"Can evolve: {can_evolve}")
print(f"Evolution IDs: {evo_ids}")

# Test 2: Create a Charmander at level 16 (exactly at evolution)
print("\nTest 2: Charmander at level 16 (at evolution threshold)")
print("-" * 60)
charmander2 = Pokemon(4, level=16)
can_evolve, evo_ids = charmander2.can_evolve()
print(f"{charmander2.name} (Level {charmander2.level})")
print(f"Evolution level: {charmander2.evolution_level}")
print(f"Evolves to ID: {charmander2.evolves_to_id}")
print(f"Can evolve: {can_evolve}")
print(f"Evolution IDs: {evo_ids}")

# Test 3: Create a Charmander at level 30 (well above evolution)
print("\nTest 3: Charmander at level 30 (above evolution threshold)")
print("-" * 60)
charmander3 = Pokemon(4, level=30)
can_evolve, evo_ids = charmander3.can_evolve()
print(f"{charmander3.name} (Level {charmander3.level})")
print(f"Evolution level: {charmander3.evolution_level}")
print(f"Evolves to ID: {charmander3.evolves_to_id}")
print(f"Can evolve: {can_evolve}")
print(f"Evolution IDs: {evo_ids}")

# Test 4: Try evolving
if can_evolve:
    print(f"\nEvolving {charmander3.name} into Pokemon ID {evo_ids[0]}...")
    evo_info = charmander3.evolve(evo_ids[0])
    print(f"SUCCESS! {evo_info['old_name']} evolved into {evo_info['new_name']}!")
    print(f"New level: {charmander3.level}")
    print(f"New evolution level: {charmander3.evolution_level}")
    print(f"New evolves_to_id: {charmander3.evolves_to_id}")
    print(f"Stat changes:")
    for stat, change in evo_info['stat_changes'].items():
        print(f"  {stat}: {change:+d}")

# Test 5: Check if Charmeleon can evolve to Charizard
print("\nTest 5: Can Charmeleon evolve to Charizard?")
print("-" * 60)
can_evolve2, evo_ids2 = charmander3.can_evolve()
print(f"{charmander3.name} (Level {charmander3.level})")
print(f"Evolution level: {charmander3.evolution_level}")
print(f"Evolves to ID: {charmander3.evolves_to_id}")
print(f"Can evolve: {can_evolve2}")
if can_evolve2:
    print(f"Evolution IDs: {evo_ids2}")

# Test 6: Pokemon that doesn't evolve
print("\nTest 6: Pokemon that doesn't evolve (Charizard)")
print("-" * 60)
charizard = Pokemon(6, level=50)
can_evolve3, evo_ids3 = charizard.can_evolve()
print(f"{charizard.name} (Level {charizard.level})")
print(f"Evolution level: {charizard.evolution_level}")
print(f"Evolves to ID: {charizard.evolves_to_id}")
print(f"Can evolve: {can_evolve3}")
print(f"Evolution IDs: {evo_ids3}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)
