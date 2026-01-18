"""
Quick verification that main game file works with learnset system
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from team_generation import TeamGenerator

def test_main_game_integration():
    """Test that main game's TeamGenerator still works"""
    print("="*80)
    print("VERIFYING MAIN GAME INTEGRATION")
    print("="*80)
    
    # This is what main.py does
    generator = TeamGenerator()
    
    # Generate an opponent team (what happens in each battle round)
    print("\nGenerating Round 1 opponent team (3 Pokemon)...")
    opponent_team = generator.generate_opponent_team(round_number=1, team_size=3)
    
    print(f"✓ Successfully generated {len(opponent_team)} Pokemon")
    
    for i, pokemon in enumerate(opponent_team, 1):
        print(f"\n{i}. {pokemon.name} (Level {pokemon.level})")
        print(f"   Type: {pokemon.type1}" + (f"/{pokemon.type2}" if pokemon.type2 else ""))
        print(f"   HP: {pokemon.max_hp}")
        print(f"   Moves: {len(pokemon.moves)} moves")
        
        # Verify moves are valid
        for move in pokemon.moves:
            assert 'name' in move, f"Move missing 'name' field: {move}"
            assert 'type' in move, f"Move missing 'type' field: {move}"
            assert 'category' in move, f"Move missing 'category' field: {move}"
            print(f"      - {move['name']} ({move['type']})")
    
    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED - Main game ready to use learnset system!")
    print("="*80)

if __name__ == "__main__":
    test_main_game_integration()
