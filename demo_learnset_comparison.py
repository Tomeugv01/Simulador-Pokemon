"""
Side-by-side comparison: Old vs New Move Assignment System
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from team_generation import TeamGenerator

def main():
    print("="*80)
    print("MOVE ASSIGNMENT SYSTEM COMPARISON")
    print("="*80)
    
    generator = TeamGenerator()
    
    print("\n📊 OLD SYSTEM (Archetype-Based Random Selection):")
    print("-"*80)
    print("❌ Moves selected randomly from type/archetype pools")
    print("❌ No level progression - Level 5 could have Thunder")
    print("❌ Inconsistent across playthroughs")
    print("❌ Not authentic to Pokemon games")
    print("\nExample (hypothetical):")
    print("  Pikachu Level 5:")
    print("    - Thunder Punch (Learn at 42)")
    print("    - Electro Ball (Learn at 18)")
    print("    - Thunder Wave (Learn at 5)")
    print("    - Tail Whip (Learn at 1)")
    
    print("\n\n✅ NEW SYSTEM (Generation-Accurate Learnsets):")
    print("-"*80)
    print("✅ Moves based on Pokemon X/Y data")
    print("✅ Level-appropriate moves only")
    print("✅ Consistent and predictable")
    print("✅ Authentic Pokemon experience")
    
    # Generate real examples
    pokemon_data = generator.pokemon_repo.get_by_id(25)  # Pikachu
    
    print("\nActual Examples:")
    
    # Level 5 Pikachu
    pikachu_5 = generator._generate_pokemon(pokemon_data, level=5)
    print(f"\n  Pikachu Level 5 (NEW SYSTEM):")
    for move in pikachu_5.moves:
        print(f"    - {move['name']}")
    
    # Level 20 Pikachu
    pikachu_20 = generator._generate_pokemon(pokemon_data, level=20)
    print(f"\n  Pikachu Level 20 (NEW SYSTEM):")
    for move in pikachu_20.moves:
        print(f"    - {move['name']}")
    
    # Level 50 Pikachu
    pikachu_50 = generator._generate_pokemon(pokemon_data, level=50)
    print(f"\n  Pikachu Level 50 (NEW SYSTEM):")
    for move in pikachu_50.moves:
        print(f"    - {move['name']}")
    
    print("\n" + "="*80)
    print("📈 PROGRESSION DEMONSTRATION")
    print("="*80)
    print("\nNotice how moves change as level increases:")
    print("  • Early levels: Basic moves (Growl, Thunder Shock)")
    print("  • Mid levels: Intermediate moves (Electro Ball, Slam)")
    print("  • High levels: Powerful moves (Thunder, Discharge)")
    
    print("\n" + "="*80)
    print("🎮 GAME IMPACT")
    print("="*80)
    print("\n✅ Round 1 opponents have weak moves (appropriate challenge)")
    print("✅ Round 10 opponents have strong moves (increased difficulty)")
    print("✅ Players recognize authentic Pokemon movesets")
    print("✅ Strategic depth - can predict opponent capabilities")
    
    print("\n" + "="*80)
    print("🎯 RESULT: Your game now uses authentic Pokemon movesets!")
    print("="*80)

if __name__ == "__main__":
    main()
