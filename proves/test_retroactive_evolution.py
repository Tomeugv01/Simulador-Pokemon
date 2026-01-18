"""
Test retroactive evolution (Pokemon already above evolution level)
"""
import sys
sys.path.append('models')
sys.path.append('src')

from Pokemon import Pokemon

print("=" * 60)
print("TESTING RETROACTIVE EVOLUTION")
print("=" * 60)

# Test: Create a Charmander at level 50 (way above both evolution levels)
print("\nTest: Charmander at level 50 (should still be able to evolve)")
print("-" * 60)
charmander = Pokemon(4, level=50)
print(f"{charmander.name} (Level {charmander.level})")
print(f"Evolution level: {charmander.evolution_level} (Charmeleon)")
print(f"Evolves to ID: {charmander.evolves_to_id}")

can_evolve, evo_ids = charmander.can_evolve()
print(f"\nCan evolve: {can_evolve}")
print(f"Evolution IDs: {evo_ids}")

if can_evolve:
    print(f"\nEvolving to Charmeleon...")
    evo_info = charmander.evolve(evo_ids[0])
    print(f"✓ {evo_info['old_name']} evolved into {evo_info['new_name']}!")
    
    # Now check if Charmeleon can immediately evolve to Charizard
    can_evolve2, evo_ids2 = charmander.can_evolve()
    print(f"\nAfter evolution: {charmander.name} (Level {charmander.level})")
    print(f"Evolution level: {charmander.evolution_level} (Charizard)")
    print(f"Can evolve again: {can_evolve2}")
    
    if can_evolve2:
        print(f"\nEvolving to Charizard...")
        evo_info2 = charmander.evolve(evo_ids2[0])
        print(f"✓ {evo_info2['old_name']} evolved into {evo_info2['new_name']}!")
        print(f"\nFinal form: {charmander.name} (Level {charmander.level})")

print("\n" + "=" * 60)
print("Retroactive evolution works! Pokemon can evolve even if")
print("they're already above the required level.")
print("=" * 60)
