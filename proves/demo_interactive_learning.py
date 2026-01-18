"""
Interactive demonstration of move learning with player choice
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from Pokemon import Pokemon

def demo_interactive():
    print("="*80)
    print("MOVE LEARNING SYSTEM - PLAYER CHOICE DEMO")
    print("="*80)
    
    print("\n📖 SCENARIO: Your Squirtle just gained enough EXP to level up!")
    print("-"*80)
    
    # Create Squirtle at level 12 with 4 moves
    squirtle = Pokemon(pokemon_id=7, level=12, moveset=[33, 39, 55, 110])
    # Tackle, Tail Whip, Water Gun, Withdraw
    
    print(f"\n{squirtle.name} - Level {squirtle.level}")
    print("Current moves:")
    for i, move in enumerate(squirtle.moves):
        power = f"Power: {move.get('power', 'N/A')}"
        category = move.get('category', 'Unknown')
        print(f"  {i+1}. {move['name']:15} ({category:8} | {power})")
    
    print("\n" + "="*80)
    print("GAINING EXPERIENCE...")
    print("="*80)
    
    # Level up to 16 (learns multiple moves)
    exp_result = squirtle.gain_exp(3000)
    
    if exp_result['leveled_up']:
        print(f"\n🎉 {squirtle.name} grew to level {exp_result['new_level']}!")
        gains = exp_result['stat_gains']
        print(f"  HP +{gains['hp']}, Atk +{gains['attack']}, Def +{gains['defense']}")
        print(f"  SpA +{gains['sp_attack']}, SpD +{gains['sp_defense']}, Spe +{gains['speed']}")
        
        # Show what moves can be learned
        print("\n" + "="*80)
        print("MOVE LEARNING")
        print("="*80)
        
        for level in range(exp_result['old_level'] + 1, exp_result['new_level'] + 1):
            new_moves = squirtle.check_moves_learned_at_level(level)
            
            for new_move in new_moves:
                # Check if already knows
                already_knows = any(m.get('id') == new_move['id'] for m in squirtle.moves)
                if already_knows:
                    print(f"\n{squirtle.name} can learn {new_move['name']}, but already knows it!")
                    continue
                
                print(f"\n✨ {squirtle.name} wants to learn {new_move['name']} (learned at level {level})!")
                
                if len(squirtle.moves) >= 4:
                    print(f"\n⚠️  But {squirtle.name} already knows 4 moves!")
                    print("\nCurrent moves:")
                    for i, move in enumerate(squirtle.moves):
                        power = move.get('power', None)
                        power_str = f"{power:>3}" if power is not None else "N/A"
                        category = move.get('category', 'Status')
                        pp = move.get('pp', '?')
                        print(f"  {i+1}. {move['name']:15} ({category:8} | Power: {power_str} | PP: {pp})")
                    
                    print(f"\n📝 Choose an action:")
                    print(f"  1-4: Replace that move with {new_move['name']}")
                    print(f"  0:   Don't learn {new_move['name']}")
                    
                    # In a real game, this would be player input
                    # For demo, we'll show what would happen with different choices
                    print("\n💡 EXAMPLE CHOICES:")
                    print(f"  • Choosing 0: {squirtle.name} would not learn {new_move['name']}")
                    print(f"  • Choosing 2: {squirtle.name} would forget Tail Whip and learn {new_move['name']}")
                    print(f"  • Choosing 3: {squirtle.name} would forget Water Gun and learn {new_move['name']}")
                    
                    # For demo, let's replace Tail Whip (index 1)
                    print(f"\n🎮 For this demo, replacing move 2 (Tail Whip)...")
                    result = squirtle.learn_move(new_move['id'], replace_index=1)
                    
                    if result['success']:
                        print(f"\n💭 {squirtle.name} forgot {result['replaced_move']['name']}...")
                        print(f"✅ And learned {new_move['name']}!")
                else:
                    result = squirtle.learn_move(new_move['id'])
                    print(f"✅ {squirtle.name} learned {new_move['name']}!")
    
    print("\n" + "="*80)
    print("FINAL RESULT")
    print("="*80)
    print(f"\n{squirtle.name} - Level {squirtle.level}")
    print("Final moveset:")
    for i, move in enumerate(squirtle.moves):
        power = f"Power: {move.get('power', 'N/A')}"
        category = move.get('category', 'Status')
        print(f"  {i+1}. {move['name']:15} ({category:8} | {power})")
    
    print("\n" + "="*80)
    print("💡 IN THE ACTUAL GAME:")
    print("="*80)
    print("✅ After each battle, when you gain EXP")
    print("✅ You'll be prompted to learn new moves")
    print("✅ You can choose which move to replace (1-4)")
    print("✅ Or skip learning the move (0)")
    print("✅ Just like in the official Pokemon games!")
    print("="*80)

if __name__ == "__main__":
    demo_interactive()
