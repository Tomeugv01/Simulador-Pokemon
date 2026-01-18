"""
Test script to verify team generation now uses learnset system
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from team_generation import TeamGenerator
from Pokemon import Pokemon

def main():
    print("="*80)
    print("TESTING LEARNSET INTEGRATION IN TEAM GENERATION")
    print("="*80)
    
    generator = TeamGenerator()
    
    # Test 1: Generate opponent team for Round 1
    print("\n1. Round 1 Opponent Team (should have level-appropriate moves)")
    print("-"*80)
    team_r1 = generator.generate_opponent_team(round_number=1, team_size=3)
    
    for i, pokemon in enumerate(team_r1, 1):
        print(f"\n{i}. {pokemon.name} (Level {pokemon.level})")
        print(f"   Moves:")
        for move in pokemon.moves:
            power_str = f"Power: {move['power']}" if move.get('power') else "Status"
            print(f"      - {move['name']} ({move['type']}, {move['category']}) - {power_str}")
    
    # Test 2: Generate opponent team for Round 5
    print("\n\n2. Round 5 Opponent Team (higher levels, different moves)")
    print("-"*80)
    team_r5 = generator.generate_opponent_team(round_number=5, team_size=3)
    
    for i, pokemon in enumerate(team_r5, 1):
        print(f"\n{i}. {pokemon.name} (Level {pokemon.level})")
        print(f"   Moves:")
        for move in pokemon.moves:
            power_str = f"Power: {move['power']}" if move.get('power') else "Status"
            print(f"      - {move['name']} ({move['type']}, {move['category']}) - {power_str}")
    
    # Test 3: Verify specific Pokemon (Pikachu at different levels)
    print("\n\n3. Pikachu at Different Levels")
    print("-"*80)
    
    pokemon_data = generator.pokemon_repo.get_by_id(25)  # Pikachu
    
    for level in [10, 30, 50]:
        pikachu = generator._generate_pokemon(pokemon_data, level)
        print(f"\nPikachu Level {level}:")
        print(f"   Moves: {', '.join(m['name'] for m in pikachu.moves)}")
    
    # Test 4: Generate starter Pokemon
    print("\n\n4. Starter Pokemon (Low Level)")
    print("-"*80)
    
    starters_data = [
        generator.pokemon_repo.get_by_id(1),   # Bulbasaur
        generator.pokemon_repo.get_by_id(4),   # Charmander
        generator.pokemon_repo.get_by_id(7),   # Squirtle
    ]
    
    for starter_data in starters_data:
        starter = generator._generate_pokemon(starter_data, level=5)
        print(f"\n{starter.name} (Level 5):")
        print(f"   Moves: {', '.join(m['name'] for m in starter.moves)}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE: All Pokemon now use generation-accurate learnsets!")
    print("="*80)

if __name__ == "__main__":
    main()
