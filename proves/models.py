"""
Model classes for Pokemon battle system.
This module now imports Pokemon and Move from the models package.
"""

import sys
import os

# Add models directory to path
models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
if models_path not in sys.path:
    sys.path.insert(0, models_path)

from Pokemon import Pokemon
from Move import Move

# Export the classes for backward compatibility
__all__ = ['Pokemon', 'Move']


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING POKEMON CLASS")
    print("=" * 70)
    
    # Create a Pikachu
    print("\n1. Creating Pikachu (Level 50) with 4 moves...")
    pikachu = Pokemon(
        pokemon_id=25,
        level=50,
        moveset=[85, 93, 99, 113]  # Some example move IDs
    )
    
    print(f"   {pikachu}")
    print(f"   Type: {pikachu.type1}")
    print(f"   Base Stats: HP:{pikachu.max_hp} Atk:{pikachu.attack} Def:{pikachu.defense} " +
          f"SpA:{pikachu.sp_attack} SpD:{pikachu.sp_defense} Spe:{pikachu.speed}")
    print(f"   Moves ({len(pikachu.moves)}):")
    for i, move in enumerate(pikachu.moves):
        print(f"      {i+1}. {move}")
    
    # Test damage
    print("\n2. Testing damage mechanics...")
    print(f"   Before damage: {pikachu}")
    damage = pikachu.take_damage(50)
    print(f"   After 50 damage: {pikachu} (dealt {damage} damage)")
    
    # Test healing
    print("\n3. Testing healing...")
    healed = pikachu.heal(30)
    print(f"   After healing 30 HP: {pikachu} (restored {healed} HP)")
    
    # Test status
    print("\n4. Testing status conditions...")
    success = pikachu.apply_status('burn')
    print(f"   Applied burn: {pikachu}")
    print(f"   Effective Attack (with burn): {pikachu.get_effective_stat('attack')} " +
          f"(base: {pikachu.attack})")
    
    # Test stat stages
    print("\n5. Testing stat stages...")
    pikachu.modify_stat_stage('attack', 2)
    print(f"   Attack +2 stages: {pikachu.get_effective_stat('attack')}")
    pikachu.modify_stat_stage('speed', -1)
    print(f"   Speed -1 stage: {pikachu.get_effective_stat('speed')}")
    
    # Test end of turn
    print("\n6. Testing end of turn effects...")
    effects = pikachu.process_end_of_turn_effects()
    print(f"   After end of turn: {pikachu}")
    print(f"   Burn damage dealt: {effects['burn_damage']}")
    
    # Create a Charizard for comparison
    print("\n7. Creating Charizard (Level 50)...")
    charizard = Pokemon(pokemon_id=6, level=50, moveset=[52, 17, 83, 115])
    print(f"   {charizard}")
    print(f"   Types: {charizard.type1}/{charizard.type2}")
    print(f"   Speed: {charizard.speed}")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed successfully!")
    print("=" * 70)
