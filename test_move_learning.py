"""
Test the move learning system
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from Pokemon import Pokemon
from database import get_moves_at_level

def test_move_learning():
    print("="*80)
    print("TESTING MOVE LEARNING SYSTEM")
    print("="*80)
    
    # Create a level 5 Pikachu with 2 moves (to test learning with < 4 moves)
    print("\n1. Testing learning moves when Pokemon has < 4 moves")
    print("-"*80)
    pikachu = Pokemon(pokemon_id=25, level=5, moveset=[84, 86])  # Thunder Shock, Thunder Wave
    
    print(f"\n{pikachu.name} Level {pikachu.level}")
    print(f"Current moves: {', '.join(m['name'] for m in pikachu.moves)}")
    
    # Check what moves Pikachu learns at level 10
    moves_at_10 = get_moves_at_level(25, 10)
    print(f"\nMoves learned at level 10: {[m['name'] for m in moves_at_10]}")
    
    # Level up to 10
    print(f"\nLeveling up to 10...")
    exp_result = pikachu.gain_exp(2000)
    print(f"New level: {pikachu.level}")
    
    # Check for new moves
    for level in range(exp_result['old_level'] + 1, exp_result['new_level'] + 1):
        new_moves = pikachu.check_moves_learned_at_level(level)
        if new_moves:
            print(f"\nAt level {level}, can learn: {[m['name'] for m in new_moves]}")
            for move in new_moves:
                if len(pikachu.moves) < 4:
                    result = pikachu.learn_move(move['id'])
                    print(f"  ✓ {result['message']}")
    
    print(f"\nCurrent moves: {', '.join(m['name'] for m in pikachu.moves)}")
    print(f"Number of moves: {len(pikachu.moves)}")
    
    # Test 2: Learning moves when Pokemon has 4 moves
    print("\n\n2. Testing learning moves when Pokemon has 4 moves")
    print("-"*80)
    
    # Create a Charmander with 4 moves
    charmander = Pokemon(pokemon_id=4, level=15, moveset=[52, 10, 43, 123])  # Ember, Scratch, Leer, Smokescreen
    print(f"\n{charmander.name} Level {charmander.level}")
    print(f"Current moves:")
    for i, move in enumerate(charmander.moves):
        print(f"  {i+1}. {move['name']}")
    
    # Check what Charmander learns at level 20
    moves_at_20 = get_moves_at_level(4, 20)
    if moves_at_20:
        print(f"\nMoves learned at level 20: {[m['name'] for m in moves_at_20]}")
        
        # Try to learn without replacement (should fail)
        print(f"\nAttempting to learn {moves_at_20[0]['name']} without replacement...")
        result = charmander.learn_move(moves_at_20[0]['id'])
        print(f"  Result: {result['message']} (Success: {result['success']})")
        
        # Learn by replacing move at index 2 (Leer)
        print(f"\nReplacing move 3 (Leer) with {moves_at_20[0]['name']}...")
        result = charmander.learn_move(moves_at_20[0]['id'], replace_index=2)
        if result['success']:
            print(f"  ✓ Forgot {result['replaced_move']['name']}")
            print(f"  ✓ {result['message']}")
        
        print(f"\nNew moveset:")
        for i, move in enumerate(charmander.moves):
            print(f"  {i+1}. {move['name']}")
    else:
        print(f"\nNo moves learned at level 20")
    
    # Test 3: Check multiple level-ups
    print("\n\n3. Testing multiple level-ups at once")
    print("-"*80)
    
    bulbasaur = Pokemon(pokemon_id=1, level=8, moveset=[33, 45])  # Tackle, Growl
    print(f"\n{bulbasaur.name} Level {bulbasaur.level}")
    print(f"Current moves: {', '.join(m['name'] for m in bulbasaur.moves)}")
    
    # Level up by 5 levels
    print(f"\nGaining 5 levels worth of EXP...")
    exp_result = bulbasaur.gain_exp(5000)
    print(f"Level {exp_result['old_level']} → {exp_result['new_level']}")
    
    # Check all moves learned in that range
    print(f"\nChecking moves learned between levels {exp_result['old_level']+1} and {exp_result['new_level']}:")
    for level in range(exp_result['old_level'] + 1, exp_result['new_level'] + 1):
        new_moves = bulbasaur.check_moves_learned_at_level(level)
        if new_moves:
            print(f"  Level {level}: {[m['name'] for m in new_moves]}")
            for move in new_moves:
                if len(bulbasaur.moves) < 4:
                    result = bulbasaur.learn_move(move['id'])
                    print(f"    ✓ {result['message']}")
    
    print(f"\nFinal moveset: {', '.join(m['name'] for m in bulbasaur.moves)}")
    
    print("\n" + "="*80)
    print("✓ ALL TESTS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_move_learning()
