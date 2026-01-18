"""
Demonstration: Move Learning in Battle
Shows how the system works when integrated into the game
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from Pokemon import Pokemon

def simulate_battle_exp():
    print("="*80)
    print("MOVE LEARNING IN GAME - DEMONSTRATION")
    print("="*80)
    
    print("\n📖 SCENARIO:")
    print("You just defeated an opponent. Your Pikachu gains EXP and levels up!")
    print("Pikachu learns new moves as it levels up.")
    print("-"*80)
    
    # Create Pikachu at level 8 with full moveset
    pikachu = Pokemon(pokemon_id=25, level=8, moveset=[84, 86, 39, 129])
    # Thunder Shock, Thunder Wave, Tail Whip, Growl
    
    print(f"\n{pikachu.name} - Level {pikachu.level}")
    print("Current moves:")
    for i, move in enumerate(pikachu.moves):
        print(f"  {i+1}. {move['name']}")
    
    print("\n💥 Battle ends! Pikachu gains 2000 EXP!")
    print("-"*80)
    
    exp_result = pikachu.gain_exp(2000)
    
    if exp_result['leveled_up']:
        print(f"\n🎉 {pikachu.name} grew to level {exp_result['new_level']}!")
        gains = exp_result['stat_gains']
        print(f"  HP +{gains['hp']}, Atk +{gains['attack']}, Def +{gains['defense']}")
        print(f"  SpA +{gains['sp_attack']}, SpD +{gains['sp_defense']}, Spe +{gains['speed']}")
        
        # Check for new moves
        for level in range(exp_result['old_level'] + 1, exp_result['new_level'] + 1):
            new_moves = pikachu.check_moves_learned_at_level(level)
            
            for new_move in new_moves:
                print(f"\n✨ {pikachu.name} wants to learn {new_move['name']}!")
                
                if len(pikachu.moves) >= 4:
                    print(f"\n⚠️  But {pikachu.name} already knows 4 moves!")
                    print("Current moves:")
                    for i, move in enumerate(pikachu.moves):
                        print(f"  {i+1}. {move['name']}")
                    
                    print(f"\n📝 PLAYER CHOICE:")
                    print(f"  1-4: Replace that move with {new_move['name']}")
                    print(f"  0:   Don't learn {new_move['name']}")
                    print("\nIn the game, you would be prompted here.")
                    print("For demo, replacing Tail Whip (move 3)...")
                    
                    result = pikachu.learn_move(new_move['id'], replace_index=2)
                    if result['success']:
                        print(f"\n💭 {pikachu.name} forgot {result['replaced_move']['name']}...")
                        print(f"✅ And learned {new_move['name']}!")
                else:
                    result = pikachu.learn_move(new_move['id'])
                    print(f"✅ {pikachu.name} learned {new_move['name']}!")
    
    print(f"\n🎯 Final moveset:")
    for i, move in enumerate(pikachu.moves):
        print(f"  {i+1}. {move['name']}")
    
    print("\n" + "="*80)
    print("💡 KEY FEATURES:")
    print("="*80)
    print("✅ Authentic Pokemon experience - learn moves at correct levels")
    print("✅ Player choice - decide which move to keep/replace")
    print("✅ Multiple moves per level - if Pokemon learns 2+ moves at same level")
    print("✅ Multi-level gains - handles learning moves across multiple levels")
    print("="*80)

if __name__ == "__main__":
    simulate_battle_exp()
