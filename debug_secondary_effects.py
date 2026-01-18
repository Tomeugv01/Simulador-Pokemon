"""Debug script for secondary effect failures"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import DatabaseManager
from models.Pokemon import Pokemon
from models.turn_logic import TurnManager, BattleAction, ActionType
from models.Move import Move

# Initialize database
db_manager = DatabaseManager()

def _create_test_pokemon(pokemon_id: int, level: int, move_ids: list):
    """Create a Pokemon with specific moves"""
    return Pokemon(pokemon_id=pokemon_id, level=level, moveset=move_ids)

def _move_obj_to_dict(move_obj):
    """Convert Move object to dictionary format"""
    return {
        'id': move_obj.id,
        'name': move_obj.name,
        'type': move_obj.type,
        'category': move_obj.category,
        'power': move_obj.power,
        'accuracy': move_obj.accuracy,
        'pp': move_obj.pp_current,
        'priority': move_obj.priority,
        'target': move_obj.target_type,
        'causes_damage': move_obj.causes_damage
    }

def _create_test_battle_state(attacker, defender):
    """Create a minimal battle state for testing"""
    return {
        'player': {
            'active_pokemon': attacker,
            'team': [attacker]
        },
        'cpu': {
            'active_pokemon': defender,
            'team': [defender]
        },
        'weather': None,
        'terrain': None,
        'turn_count': 1
    }

def debug_move(move_name):
    """Debug a specific move's secondary effects"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING: {move_name}")
    print('='*80)
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Get move info
    cursor.execute("""
        SELECT m.id, m.name, m.category, m.power,
               mei.probability, me.effect_type, me.status_condition, me.name as effect_name
        FROM moves m
        JOIN move_effect_instances mei ON m.id = mei.move_id
        JOIN move_effects me ON mei.effect_id = me.id
        WHERE m.name = ?
    """, (move_name,))
    
    rows = cursor.fetchall()
    
    if not rows:
        print(f"ERROR: Move '{move_name}' not found in database")
        return
    
    print(f"\nDatabase entries for {move_name}:")
    for row in rows:
        move_id, name, category, power, probability, effect_type, status_condition, effect_name = row
        print(f"  - Effect: {effect_name}")
        print(f"  - Type: {effect_type}")
        print(f"  - Probability: {probability}%")
        print(f"  - Status: {status_condition}")
        print(f"  - Move ID: {move_id}")
    
    # Test the move
    move_id = rows[0][0]
    print(f"\nTesting move {move_id} ({move_name})...")
    
    effects_triggered = []
    for run in range(30):
        attacker = _create_test_pokemon(100, 50, [move_id])
        defender = _create_test_pokemon(100, 50, [1])
        
        attacker_move = _move_obj_to_dict(attacker.moves[0])
        defender_move = _move_obj_to_dict(defender.moves[0])
        
        battle_state = _create_test_battle_state(attacker, defender)
        turn_manager = TurnManager(battle_state)
        
        # Record initial state
        initial_status = defender.status
        initial_stat_stages = defender.stat_stages.copy()
        
        action = BattleAction(
            pokemon=attacker,
            action_type=ActionType.FIGHT,
            move=attacker_move,
            target=defender
        )
        
        dummy_action = BattleAction(
            pokemon=defender,
            action_type=ActionType.FIGHT,
            move=defender_move,
            target=attacker
        )
        
        result = turn_manager.execute_turn([action, dummy_action])
        
        # Check what changed
        effect_info = {
            'run': run + 1,
            'status_changed': defender.status != initial_status,
            'new_status': defender.status,
            'stat_changes': {},
            'turn_log': result['turn_log']
        }
        
        for stat in initial_stat_stages:
            if defender.stat_stages[stat] != initial_stat_stages[stat]:
                effect_info['stat_changes'][stat] = {
                    'before': initial_stat_stages[stat],
                    'after': defender.stat_stages[stat]
                }
        
        # Check for flinch in log
        has_flinch = any('flinch' in log.lower() for log in result['turn_log'])
        effect_info['flinched'] = has_flinch
        
        if effect_info['status_changed'] or effect_info['stat_changes'] or has_flinch:
            effects_triggered.append(effect_info)
    
    print(f"\nEffects triggered: {len(effects_triggered)}/30 runs ({len(effects_triggered)/30*100:.1f}%)")
    
    if effects_triggered:
        print("\nSample triggers:")
        for i, effect in enumerate(effects_triggered[:5]):
            print(f"\n  Run {effect['run']}:")
            if effect['status_changed']:
                print(f"    Status: {effect['new_status']}")
            if effect['stat_changes']:
                print(f"    Stat changes: {effect['stat_changes']}")
            if effect['flinched']:
                print(f"    Flinched!")
            print(f"    Log: {effect['turn_log']}")
    else:
        print("\nNO EFFECTS TRIGGERED!")
        print("Sample turn log from last run:")
        for log in result['turn_log']:
            print(f"  {log}")
    
    conn.close()

if __name__ == "__main__":
    failed_moves = [
        "Thunder Fang",
        "Ice Fang",
        "Poison Fang",
        "Iron Head",
        "Fake Out",
        "Thunderbolt"
    ]
    
    for move_name in failed_moves:
        debug_move(move_name)
        print()
