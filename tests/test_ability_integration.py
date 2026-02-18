"""
Comprehensive test for ability integration into turn_logic.py
Tests that abilities correctly hook into the battle system.
"""
import sys
import os
import random

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.Pokemon import Pokemon
from models.turn_logic import TurnManager, BattleAction, ActionType
from models.ability import AbilityHandler

# Fix random seed for reproducible tests
random.seed(42)

def create_test_pokemon(name, types, ability, stats=None, level=50):
    """Create a simple test Pokemon with overridden ability"""
    p = Pokemon.__new__(Pokemon)
    p.name = name
    p.id = 1
    p.pokedex_id = 1
    p.level = level
    p.type1 = types[0]
    p.type2 = types[1] if len(types) > 1 else None
    p.ability = ability
    p.ability_id = 1
    p.status = None
    p.current_hp = 200
    p.max_hp = 200
    p.held_item = None
    
    # Base stats
    base = stats or {'hp': 200, 'attack': 100, 'defense': 100, 'sp_attack': 100, 'sp_defense': 100, 'speed': 100}
    p.hp = base.get('hp', 200)
    p.attack = base.get('attack', 100)
    p.defense = base.get('defense', 100)
    p.sp_attack = base.get('sp_attack', 100)
    p.sp_defense = base.get('sp_defense', 100)
    p.speed = base.get('speed', 100)
    
    # Stat stages
    p.stat_stages = {
        'attack': 0, 'defense': 0, 'sp_attack': 0,
        'sp_defense': 0, 'speed': 0, 'accuracy': 0, 'evasion': 0
    }
    
    # Volatile conditions
    p.confused = False
    p.flinched = False
    p.trapped = False
    p.protected = False
    p.turns_active = 0
    p.focus_energy = False
    p.substitute = None
    
    # Methods
    def get_eff(stat_name):
        base_val = getattr(p, stat_name)
        stage = p.stat_stages.get(stat_name, 0)
        if stage >= 0:
            mult = (2 + stage) / 2
        else:
            mult = 2 / (2 - stage)
        return int(base_val * mult)
    
    p.get_effective_stat = get_eff
    
    def take_dmg(amount):
        p.current_hp = max(0, p.current_hp - amount)
    p.take_damage = take_dmg
    
    def apply_stat(name):
        p.status = name
    p.apply_status = apply_stat
    
    def mod_stage(stat, amount):
        p.stat_stages[stat] = max(-6, min(6, p.stat_stages.get(stat, 0) + amount))
    p.modify_stat_stage = mod_stage
    
    def can_use(move):
        return True
    p.can_use_move = can_use
    
    def reset_volatile():
        p.confused = False
        p.flinched = False
        p.trapped = False
        p.protected = False
    p.reset_volatile_conditions = reset_volatile
    
    return p

def create_battle_state(p1, p2):
    """Create a basic battle state"""
    return {
        'player1_active': p1,
        'player2_active': p2,
        'player1_team': [p1],
        'player2_team': [p2],
        'weather': {'type': 'None', 'turns_remaining': 0},
        'field_effects': {},
        'player1_side_effects': {},
        'player2_side_effects': {},
        'turn_count': 0
    }

def create_move(name, move_type, power, category='Physical', accuracy=100, effects=None, causes_damage=True, priority=0):
    return {
        'id': 1,
        'name': name,
        'type': move_type,
        'power': power,
        'category': category,
        'accuracy': accuracy,
        'effects': effects or [],
        'causes_damage': causes_damage,
        'priority': priority,
        'never_miss': False
    }

# Track test results
passed = 0
failed = 0

def test(name, condition, details=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} {details}")

print("=" * 60)
print("ABILITY INTEGRATION TESTS")
print("=" * 60)

# ==========================================
# Test 1: Levitate (Ground Immunity)
# ==========================================
print("\n--- Test: Levitate (Ground Immunity) ---")
random.seed(42)
attacker = create_test_pokemon("Garchomp", ["Dragon", "Ground"], "Rough Skin")
defender = create_test_pokemon("Rotom", ["Electric", "Ghost"], "Levitate")
state = create_battle_state(attacker, defender)
tm = TurnManager(state)
move = create_move("Earthquake", "Ground", 100)
damage, crit = tm._calculate_damage(attacker, defender, move)
test("Levitate blocks Ground moves", damage == 0, f"damage={damage}")

# ==========================================
# Test 2: Flash Fire (Fire Immunity + Boost)
# ==========================================
print("\n--- Test: Flash Fire (Fire Immunity + Boost) ---")
random.seed(42)
attacker = create_test_pokemon("Charizard", ["Fire", "Flying"], "Blaze")
defender = create_test_pokemon("Heatran", ["Fire", "Steel"], "Flash Fire")
state = create_battle_state(attacker, defender)
tm = TurnManager(state)
move = create_move("Flamethrower", "Fire", 90, "Special")
damage, crit = tm._calculate_damage(attacker, defender, move)
test("Flash Fire blocks Fire moves", damage == 0, f"damage={damage}")
test("Flash Fire activates boost", getattr(defender, 'flash_fire_active', False))

# ==========================================
# Test 3: Water Absorb (Water Immunity + Heal)
# ==========================================
print("\n--- Test: Water Absorb (Water Immunity + Heal) ---")
random.seed(42)
attacker = create_test_pokemon("Blastoise", ["Water"], "Torrent")
defender = create_test_pokemon("Vaporeon", ["Water"], "Water Absorb")
defender.current_hp = 100  # Take some damage first
state = create_battle_state(attacker, defender)
tm = TurnManager(state)
move = create_move("Water Gun", "Water", 40, "Special")
damage, crit = tm._calculate_damage(attacker, defender, move)
test("Water Absorb blocks Water moves", damage == 0, f"damage={damage}")
test("Water Absorb heals", defender.current_hp > 100, f"hp={defender.current_hp}")

# ==========================================
# Test 4: Sturdy (Survive OHKO)
# ==========================================
print("\n--- Test: Sturdy (Survive OHKO) ---")
random.seed(10)  # Seed that doesn't crit
attacker = create_test_pokemon("Machamp", ["Fighting"], "Guts",
                                stats={'hp': 200, 'attack': 250, 'defense': 100, 'sp_attack': 100, 'sp_defense': 100, 'speed': 100})
defender = create_test_pokemon("Golem", ["Rock", "Ground"], "Sturdy",
                                stats={'hp': 150, 'attack': 100, 'defense': 100, 'sp_attack': 100, 'sp_defense': 100, 'speed': 100})
defender.current_hp = defender.max_hp  # Full HP
state = create_battle_state(attacker, defender)
tm = TurnManager(state)
move = create_move("Close Combat", "Fighting", 120)
damage, crit = tm._calculate_damage(attacker, defender, move)
test("Sturdy caps lethal damage", damage < defender.max_hp if damage >= defender.max_hp - 1 else True,
     f"damage={damage}, max_hp={defender.max_hp}")

# ==========================================
# Test 5: Intimidate (Switch-in Atk drop)
# ==========================================
print("\n--- Test: Intimidate (Switch-in) ---")
random.seed(42)
attacker = create_test_pokemon("Gyarados", ["Water", "Flying"], "Intimidate")
defender = create_test_pokemon("Pikachu", ["Electric"], "Static")
state = create_battle_state(attacker, defender)
tm = TurnManager(state)
tm._trigger_switch_in_ability(attacker)
test("Intimidate lowers opponent Attack", defender.stat_stages['attack'] == -1,
     f"stage={defender.stat_stages['attack']}")

# ==========================================
# Test 6: Compound Eyes (Accuracy boost)
# ==========================================
print("\n--- Test: Compound Eyes (Accuracy) ---")
random.seed(42)
attacker = create_test_pokemon("Butterfree", ["Bug", "Flying"], "Compound Eyes")
defender = create_test_pokemon("Pidgey", ["Normal", "Flying"], None)
state = create_battle_state(attacker, defender)
tm = TurnManager(state)
move = create_move("Sleep Powder", "Grass", 0, "Status", accuracy=75, causes_damage=False)
# Test accuracy modification
accuracy, always_hit = AbilityHandler.modify_accuracy(attacker, defender, 75, move, state)
test("Compound Eyes boosts accuracy", accuracy == 97, f"accuracy={accuracy}")

# ==========================================
# Test 7: No Guard (Always hits)
# ==========================================
print("\n--- Test: No Guard (Always hits) ---")
attacker = create_test_pokemon("Machamp", ["Fighting"], "No Guard")
defender = create_test_pokemon("Pidgey", ["Normal", "Flying"], None)
state = create_battle_state(attacker, defender)
accuracy, always_hit = AbilityHandler.modify_accuracy(attacker, defender, 70, {}, state)
test("No Guard always hits", always_hit)

# ==========================================
# Test 8: Swift Swim (Speed in Rain)
# ==========================================
print("\n--- Test: Swift Swim (Speed in Rain) ---")
swimmer = create_test_pokemon("Ludicolo", ["Water", "Grass"], "Swift Swim")
state = {'weather': {'type': 'Rain', 'turns_remaining': 5}}
speed = AbilityHandler.modify_speed(swimmer, 100, state)
test("Swift Swim doubles speed in Rain", speed == 200, f"speed={speed}")

# ==========================================
# Test 9: Huge Power (Attack boost)
# ==========================================
print("\n--- Test: Huge Power (Attack boost) ---")
attacker = create_test_pokemon("Azumarill", ["Water", "Fairy"], "Huge Power")
defender = create_test_pokemon("Pidgey", ["Normal", "Flying"], None)
move = create_move("Play Rough", "Fairy", 90)
state = create_battle_state(attacker, defender)
power, multiplier, extra = AbilityHandler.modify_outgoing_damage(
    attacker, defender, move, 90, 0, 1.0, state, False)
test("Huge Power doubles physical attack", multiplier == 2.0, f"mult={multiplier}")

# ==========================================
# Test 10: Inner Focus (Flinch immunity)
# ==========================================
print("\n--- Test: Inner Focus (Flinch prevention) ---")
pokemon = create_test_pokemon("Lucario", ["Fighting", "Steel"], "Inner Focus")
logs = []
prevented = AbilityHandler.on_flinch(pokemon, lambda m: logs.append(m))
test("Inner Focus prevents flinch", prevented)

# ==========================================
# Test 11: Rock Head (Recoil immunity)
# ==========================================
print("\n--- Test: Rock Head (Recoil immunity) ---")
pokemon = create_test_pokemon("Aggron", ["Steel", "Rock"], "Rock Head")
immune = AbilityHandler.check_recoil_immunity(pokemon)
test("Rock Head blocks recoil", immune)

# ==========================================
# Test 12: Status immunnity abilities
# ==========================================
print("\n--- Test: Status immunity abilities ---")
pokemon = create_test_pokemon("Muk", ["Poison"], "Immunity")
blocked = AbilityHandler.check_status_immunity(pokemon, 'poison')
test("Immunity blocks poison", blocked)

pokemon2 = create_test_pokemon("Persian", ["Normal"], "Limber")
blocked2 = AbilityHandler.check_status_immunity(pokemon2, 'paralysis')
test("Limber blocks paralysis", blocked2)

# ==========================================
# Test 13: Clear Body (Stat drop immunity)
# ==========================================
print("\n--- Test: Clear Body (Stat drop blocking) ---")
pokemon = create_test_pokemon("Metagross", ["Steel", "Psychic"], "Clear Body")
is_blocked, counter = AbilityHandler.check_stat_drop_immunity(pokemon, 'attack', -1)
test("Clear Body blocks stat drops", is_blocked)

# ==========================================
# Test 14: Contrary (Stat inversion)
# ==========================================
print("\n--- Test: Contrary (Stat inversion) ---")
change = AbilityHandler.modify_stat_change(
    create_test_pokemon("Serperior", ["Grass"], "Contrary"), 'sp_attack', -2)
test("Contrary inverts stat change", change == 2, f"change={change}")

# ==========================================
# Test 15: Adaptability (STAB 2.0)
# ==========================================
print("\n--- Test: Adaptability (Enhanced STAB) ---")
stab = AbilityHandler.modify_stab(
    create_test_pokemon("Porygon-Z", ["Normal"], "Adaptability"), 1.5)
test("Adaptability gives 2.0 STAB", stab == 2.0, f"stab={stab}")

# ==========================================
# Test 16: Battle Armor (Crit block)
# ==========================================
print("\n--- Test: Battle Armor (Crit block) ---")
stage, blocked = AbilityHandler.modify_crit_stage(
    create_test_pokemon("Attacker", ["Normal"], None),
    create_test_pokemon("Drapion", ["Poison", "Dark"], "Battle Armor"),
    0)
test("Battle Armor blocks crits", blocked)

# ==========================================ber
# Test 17: Shadow Tag (Trapping)
# ==========================================
print("\n--- Test: Shadow Tag (Trapping) ---")
trapper = create_test_pokemon("Wobbuffet", ["Psychic"], "Shadow Tag")
trapped = create_test_pokemon("Pidgey", ["Normal", "Flying"], "Keen Eye")
is_trapped = AbilityHandler.check_trapping(trapper, trapped, {}, lambda m: None)
test("Shadow Tag traps opponent", is_trapped)

# ==========================================
# Test 18: Sand Stream sets Sandstorm on switch-in
# ==========================================
print("\n--- Test: Sand Stream (Weather on switch-in) ---")
random.seed(42)
tyranitar = create_test_pokemon("Tyranitar", ["Rock", "Dark"], "Sand Stream")
opponent = create_test_pokemon("Pikachu", ["Electric"], "Static")
state = create_battle_state(tyranitar, opponent)
tm = TurnManager(state)
tm._trigger_switch_in_ability(tyranitar)
weather = state.get('weather', {}).get('type')
test("Sand Stream sets Sandstorm", weather == 'Sandstorm', f"weather={weather}")

# ==========================================
# Test 19: Full integration - execute_move with contact ability
# ==========================================
print("\n--- Test: Contact ability triggers in _execute_move ---")
random.seed(1)
attacker = create_test_pokemon("Kangaskhan", ["Normal"], "Scrappy",
                                stats={'hp': 200, 'attack': 120, 'defense': 100, 'sp_attack': 80, 'sp_defense': 100, 'speed': 100})
defender = create_test_pokemon("Electrode", ["Electric"], "Static")
state = create_battle_state(attacker, defender)
tm = TurnManager(state)
move = create_move("Return", "Normal", 102)
# Run many times to see if Static triggers
triggered = False
for i in range(20):
    random.seed(i)
    attacker2 = create_test_pokemon("Kangaskhan", ["Normal"], "Scrappy",
                                    stats={'hp': 200, 'attack': 120, 'defense': 100, 'sp_attack': 80, 'sp_defense': 100, 'speed': 100})
    defender2 = create_test_pokemon("Electrode", ["Electric"], "Static")
    sa = create_battle_state(attacker2, defender2)
    tm2 = TurnManager(sa)
    tm2._execute_move(attacker2, move, defender2)
    if attacker2.status == 'paralysis':
        triggered = True
        break
test("Static can trigger on contact", triggered)

# ==========================================
# Test 20: Weather immunity - Sandstorm
# ==========================================
print("\n--- Test: Weather immunity (Overcoat in Sandstorm) ---")
pokemon = create_test_pokemon("Forretress", ["Bug", "Steel"], "Overcoat")
immune = AbilityHandler.check_weather_immunity(pokemon, 'Sandstorm')
test("Overcoat blocks Sandstorm damage", immune)

# ==========================================
# Test 21: Moxie on KO
# ==========================================
print("\n--- Test: Moxie (Attack boost on KO) ---")
attacker = create_test_pokemon("Salamence", ["Dragon", "Flying"], "Moxie")
logs = []
AbilityHandler.on_ko(attacker, lambda m: logs.append(m))
test("Moxie raises Attack on KO", attacker.stat_stages['attack'] == 1,
     f"stage={attacker.stat_stages['attack']}")

# ==========================================
# Test 22: Disguise blocks first hit
# ==========================================
print("\n--- Test: Disguise (Blocks first hit) ---")
defender = create_test_pokemon("Mimikyu", ["Ghost", "Fairy"], "Disguise")
defender.disguise_broken = False
logs = []
blocked = AbilityHandler.check_disguise(defender, {}, lambda m: logs.append(m))
test("Disguise blocks first hit", blocked)
test("Disguise breaks after", defender.disguise_broken)

# ==========================================
# Summary
# ==========================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed}/{passed + failed} tests passed")
if failed > 0:
    print(f"  {failed} test(s) FAILED")
else:
    print("  All tests PASSED!")
print("=" * 60)
