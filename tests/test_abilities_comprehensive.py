"""
Comprehensive Ability Integration Tests
Tests all ability trigger points across the full battle system:
  - Type immunities & absorb abilities
  - Damage modification (attacker & defender)
  - Stat change modification (Contrary, Simple, Clear Body, Defiant, Competitive)
  - Status immunity
  - Contact abilities
  - Switch-in / Switch-out abilities
  - Speed / Accuracy / Crit modifiers
  - Weather & end-of-turn abilities
  - KO-triggered abilities
  - Special mechanics (Disguise, Sturdy, Magic Bounce, Protean, Mold Breaker, Parental Bond, Skill Link)
  - Full turn integration (execute_turn with ability interactions)
"""
import sys
import os
import random

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.Pokemon import Pokemon
from models.turn_logic import TurnManager, BattleAction, ActionType
from models.ability import AbilityHandler, CONTACT_OVERRIDE_NO

# ============================================================
# TEST UTILITIES
# ============================================================

_passed = 0
_failed = 0
_section = ""


def section(name):
    global _section
    _section = name
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")


def test(name, condition, details=""):
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS: {name}")
    else:
        _failed += 1
        print(f"  FAIL: {name} â€” {details}")


def create_pokemon(name, types, ability, stats=None, level=50, status=None):
    """Create a lightweight test Pokemon with overridden attributes."""
    p = Pokemon.__new__(Pokemon)
    p.name = name
    p.id = 1
    p.pokedex_id = 1
    p.level = level
    p.type1 = types[0]
    p.type2 = types[1] if len(types) > 1 else None
    p.ability = ability
    p.ability_id = 1
    p.status = status
    p.held_item = None

    base = stats or {}
    p.max_hp = base.get('hp', 200)
    p.current_hp = p.max_hp
    p.hp = p.max_hp
    p.attack = base.get('attack', 100)
    p.defense = base.get('defense', 100)
    p.sp_attack = base.get('sp_attack', 100)
    p.sp_defense = base.get('sp_defense', 100)
    p.speed = base.get('speed', 100)

    p.stat_stages = {
        'attack': 0, 'defense': 0, 'sp_attack': 0,
        'sp_defense': 0, 'speed': 0, 'accuracy': 0, 'evasion': 0
    }

    # Volatile / semi-volatile conditions
    p.confused = False
    p.confusion_turns = 0
    p.flinched = False
    p.charging = False
    p.recharging = False
    p.trapped = False
    p.trap_turns = 0
    p.seeded = False
    p.protected = False
    p.turns_active = 0
    p.substitute = False
    p.substitute_hp = 0
    p.encore = False
    p.encore_turns = 0
    p.encore_move = None
    p.taunted = False
    p.taunt_turns = 0
    p.disabled_move = None
    p.disable_turns = 0
    p.tormented = False
    p.last_move_used = None
    p.cursed = False
    p.ingrain = False
    p.aqua_ring = False
    p.transformed = False
    p.original_stats = None
    p.embargo = False
    p.embargo_turns = 0
    p.heal_block = False
    p.heal_block_turns = 0
    p.yawn = False
    p.yawn_turns = 0
    p.focus_energy = False
    p.fainted = False
    p.moves = []
    p.sleep_turns = 0
    p.toxic_counter = 1

    def get_eff(stat_name):
        base_val = getattr(p, stat_name)
        stage = p.stat_stages.get(stat_name, 0)
        if stage >= 0:
            mult = (2 + stage) / 2
        else:
            mult = 2 / (2 - stage)
        return int(base_val * mult)

    p.get_effective_stat = get_eff
    p.take_damage = lambda amt: setattr(p, 'current_hp', max(0, p.current_hp - amt)) or None
    p.heal = lambda amt: setattr(p, 'current_hp', min(p.max_hp, p.current_hp + amt)) or None
    p.apply_status = lambda s, *a: setattr(p, 'status', s) or None
    p.cure_status = lambda: setattr(p, 'status', None) or None
    p.modify_stat_stage = lambda stat, amount: p.stat_stages.__setitem__(
        stat, max(-6, min(6, p.stat_stages.get(stat, 0) + amount)))
    p.can_use_move = lambda m: True
    p.reset_volatile_conditions = lambda: [
        setattr(p, 'confused', False), setattr(p, 'flinched', False),
        setattr(p, 'trapped', False), setattr(p, 'protected', False)]
    p.get_stat_changes_display = lambda: ""

    def _process_end_of_turn():
        """Minimal version of process_end_of_turn_effects for test mocks."""
        effects = {}
        if p.status == 'burn':
            dmg = max(1, p.max_hp // 16)
            p.take_damage(dmg)
            effects['burn_damage'] = dmg
        elif p.status == 'poison':
            dmg = max(1, p.max_hp // 8)
            p.take_damage(dmg)
            effects['poison_damage'] = dmg
        elif p.status == 'badly_poison':
            dmg = max(1, (p.max_hp * p.toxic_counter) // 16)
            p.take_damage(dmg)
            p.toxic_counter += 1
            effects['poison_damage'] = dmg
        if p.trapped and p.trap_turns > 0:
            dmg = max(1, p.max_hp // 16)
            p.take_damage(dmg)
            effects['trap_damage'] = dmg
            p.trap_turns -= 1
            if p.trap_turns <= 0:
                p.trapped = False
        if p.seeded:
            dmg = max(1, p.max_hp // 8)
            p.take_damage(dmg)
            effects['leech_seed_damage'] = dmg
        if p.cursed:
            dmg = max(1, p.max_hp // 4)
            p.take_damage(dmg)
            effects['curse_damage'] = dmg
        if p.aqua_ring:
            heal = max(1, p.max_hp // 16)
            p.heal(heal)
            effects['aqua_ring_heal'] = heal
        if p.ingrain:
            heal = max(1, p.max_hp // 16)
            p.heal(heal)
            effects['ingrain_heal'] = heal
        if p.encore:
            p.encore_turns -= 1
            if p.encore_turns <= 0:
                p.encore = False
                p.encore_move = None
        if p.taunted:
            p.taunt_turns -= 1
            if p.taunt_turns <= 0:
                p.taunted = False
        if p.disabled_move:
            p.disable_turns -= 1
            if p.disable_turns <= 0:
                p.disabled_move = None
        if p.embargo:
            p.embargo_turns -= 1
            if p.embargo_turns <= 0:
                p.embargo = False
        if p.heal_block:
            p.heal_block_turns -= 1
            if p.heal_block_turns <= 0:
                p.heal_block = False
        if p.yawn:
            p.yawn_turns -= 1
            if p.yawn_turns <= 0:
                p.yawn = False
        return effects

    p.process_end_of_turn_effects = _process_end_of_turn

    def _can_move():
        if p.fainted:
            return False, "fainted"
        if p.status == 'sleep':
            return False, "sleep"
        if p.status == 'freeze':
            return False, "freeze"
        if p.recharging:
            p.recharging = False
            return False, "recharging"
        return True, None

    p.can_move = _can_move
    p.has_type = lambda t: p.type1 == t or p.type2 == t

    return p


def make_move(name, mtype, power, category='Physical', accuracy=100,
              effects=None, causes_damage=True, priority=0):
    return {
        'id': 1, 'name': name, 'type': mtype, 'power': power,
        'category': category, 'accuracy': accuracy,
        'effects': effects or [], 'causes_damage': causes_damage,
        'priority': priority, 'never_miss': False,
    }


def battle_state(p1, p2):
    return {
        'player1_active': p1, 'player2_active': p2,
        'player1_team': [p1], 'player2_team': [p2],
        'weather': {'type': 'None', 'turns_remaining': 0},
        'field_effects': {},
        'player1_side_effects': {}, 'player2_side_effects': {},
        'turn_count': 1,
    }


# ============================================================
# 1. TYPE IMMUNITY & ABSORB ABILITIES
# ============================================================
section("Type Immunity & Absorb Abilities")

# -- Levitate --
random.seed(42)
a = create_pokemon("Attacker", ["Ground"], None)
d = create_pokemon("Def-Levitate", ["Electric"], "Levitate")
st = battle_state(a, d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(a, d, make_move("Earthquake", "Ground", 100))
test("Levitate blocks Ground", dmg == 0)

# -- Flash Fire --
random.seed(42)
a = create_pokemon("Atk", ["Fire"], None)
d = create_pokemon("Def-FF", ["Fire"], "Flash Fire")
st = battle_state(a, d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(a, d, make_move("Flamethrower", "Fire", 90, "Special"))
test("Flash Fire blocks Fire", dmg == 0)
test("Flash Fire activates flag", getattr(d, 'flash_fire_active', False))

# -- Water Absorb --
random.seed(42)
d = create_pokemon("Def-WA", ["Water"], "Water Absorb")
d.current_hp = 100
st = battle_state(create_pokemon("A", ["Water"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Surf", "Water", 90, "Special"))
test("Water Absorb blocks Water", dmg == 0)
test("Water Absorb heals", d.current_hp > 100, f"hp={d.current_hp}")

# -- Volt Absorb --
random.seed(42)
d = create_pokemon("Def-VA", ["Electric"], "Volt Absorb")
d.current_hp = 150
st = battle_state(create_pokemon("A", ["Electric"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Thunderbolt", "Electric", 90, "Special"))
test("Volt Absorb blocks Electric", dmg == 0)
test("Volt Absorb heals", d.current_hp > 150, f"hp={d.current_hp}")

# -- Motor Drive --
random.seed(42)
d = create_pokemon("Def-MD", ["Electric"], "Motor Drive")
st = battle_state(create_pokemon("A", ["Electric"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Thunderbolt", "Electric", 90, "Special"))
test("Motor Drive blocks Electric", dmg == 0)
test("Motor Drive boosts Speed", d.stat_stages['speed'] == 1, f"stage={d.stat_stages['speed']}")

# -- Sap Sipper --
random.seed(42)
d = create_pokemon("Def-SS", ["Normal"], "Sap Sipper")
st = battle_state(create_pokemon("A", ["Grass"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Razor Leaf", "Grass", 55))
test("Sap Sipper blocks Grass", dmg == 0)
test("Sap Sipper boosts Attack", d.stat_stages['attack'] == 1, f"stage={d.stat_stages['attack']}")

# -- Lightning Rod --
random.seed(42)
d = create_pokemon("Def-LR", ["Ground"], "Lightning Rod")
st = battle_state(create_pokemon("A", ["Electric"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Thunderbolt", "Electric", 90, "Special"))
test("Lightning Rod blocks Electric", dmg == 0)
test("Lightning Rod boosts SpAtk", d.stat_stages['sp_attack'] == 1, f"stage={d.stat_stages['sp_attack']}")

# -- Storm Drain --
random.seed(42)
d = create_pokemon("Def-SD", ["Rock"], "Storm Drain")
st = battle_state(create_pokemon("A", ["Water"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Surf", "Water", 90, "Special"))
test("Storm Drain blocks Water", dmg == 0)
test("Storm Drain boosts SpAtk", d.stat_stages['sp_attack'] == 1, f"stage={d.stat_stages['sp_attack']}")

# -- Dry Skin (Water immunity + Fire weakness) --
random.seed(42)
d = create_pokemon("Def-DrySkin", ["Poison"], "Dry Skin")
d.current_hp = 100
st = battle_state(create_pokemon("A", ["Water"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Surf", "Water", 90, "Special"))
test("Dry Skin blocks Water", dmg == 0)
test("Dry Skin heals from Water", d.current_hp > 100, f"hp={d.current_hp}")

# -- Wonder Guard --
random.seed(42)
d = create_pokemon("Shedinja", ["Bug", "Ghost"], "Wonder Guard")
a_good = create_pokemon("AtkFire", ["Fire"], None)
st = battle_state(a_good, d)
tm = TurnManager(st)
dmg_fire, _ = tm._calculate_damage(a_good, d, make_move("Flamethrower", "Fire", 90, "Special"))
test("Wonder Guard allows SE moves", dmg_fire > 0, f"dmg={dmg_fire}")

random.seed(42)
a_bad = create_pokemon("AtkNorm", ["Normal"], None)
st2 = battle_state(a_bad, create_pokemon("Shedinja2", ["Bug", "Ghost"], "Wonder Guard"))
tm2 = TurnManager(st2)
dmg_norm, _ = tm2._calculate_damage(a_bad, st2['player2_active'], make_move("Tackle", "Normal", 40))
test("Wonder Guard blocks non-SE moves", dmg_norm == 0, f"dmg={dmg_norm}")

# -- Bulletproof --
random.seed(42)
d = create_pokemon("Def-BP", ["Grass"], "Bulletproof")
st = battle_state(create_pokemon("A", ["Normal"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Shadow Ball", "Ghost", 80, "Special"))
test("Bulletproof blocks ball/bomb moves", dmg == 0, f"dmg={dmg}")

# -- Soundproof --
random.seed(42)
d = create_pokemon("Def-SP", ["Normal"], "Soundproof")
st = battle_state(create_pokemon("A", ["Normal"], None), d)
tm = TurnManager(st)
dmg, _ = tm._calculate_damage(st['player1_active'], d, make_move("Hyper Voice", "Normal", 90, "Special"))
test("Soundproof blocks sound moves", dmg == 0, f"dmg={dmg}")


# ============================================================
# 2. ATTACKER DAMAGE ABILITIES
# ============================================================
section("Attacker Damage Modification")

# -- Huge Power --
a = create_pokemon("Azumarill", ["Water", "Fairy"], "Huge Power")
m = make_move("Play Rough", "Fairy", 90)
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), m, 90, 0, 1.0, {})
test("Huge Power 2x physical", mult == 2.0, f"mult={mult}")

# -- Pure Power --
a = create_pokemon("Medicham", ["Fighting", "Psychic"], "Pure Power")
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Hi Jump Kick", "Fighting", 130), 130, 0, 1.0, {})
test("Pure Power 2x physical", mult == 2.0, f"mult={mult}")

# -- Technician --
a = create_pokemon("Scizor", ["Bug", "Steel"], "Technician")
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Bullet Punch", "Steel", 40), 40, 0, 1.0, {})
test("Technician 1.5x on <=60 BP", mult == 1.5, f"mult={mult}")

# Technician should NOT boost high BP
_, mult2, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("X-Scissor", "Bug", 80), 80, 0, 1.0, {})
test("Technician no boost on >60 BP", mult2 == 1.0, f"mult={mult2}")

# -- Iron Fist --
a = create_pokemon("Pangoro", ["Fighting", "Dark"], "Iron Fist")
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Hammer Arm", "Fighting", 100), 100, 0, 1.0, {})
test("Iron Fist boosts punch moves", mult == 1.2, f"mult={mult}")

# -- Strong Jaw --
a = create_pokemon("Tyrantrum", ["Rock", "Dragon"], "Strong Jaw")
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Crunch", "Dark", 80), 80, 0, 1.0, {})
test("Strong Jaw boosts bite moves", mult == 1.5, f"mult={mult}")

# -- Mega Launcher --
a = create_pokemon("Clawitzer", ["Water"], "Mega Launcher")
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Dark Pulse", "Dark", 80, "Special"), 80, 0, 1.0, {})
test("Mega Launcher boosts pulse moves", mult == 1.5, f"mult={mult}")

# -- Tough Claws (contact) --
a = create_pokemon("Metagross", ["Steel", "Psychic"], "Tough Claws")
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Meteor Mash", "Steel", 90), 90, 0, 1.0, {}, is_contact=True)
test("Tough Claws 1.3x on contact", mult == 1.3, f"mult={mult}")

# -- Guts --
a = create_pokemon("Machamp", ["Fighting"], "Guts", status='burn')
a.status = 'burn'
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Close Combat", "Fighting", 120), 120, 0, 1.0, {})
test("Guts 1.5x when statused", mult == 1.5, f"mult={mult}")
test("Guts negates burn attack reduction", AbilityHandler.check_burn_attack_reduction(a))

# -- Blaze/Torrent/Overgrow/Swarm (at 1/3 HP) --
a = create_pokemon("Charizard", ["Fire", "Flying"], "Blaze")
a.current_hp = a.max_hp // 3  # at threshold
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Flamethrower", "Fire", 90, "Special"), 90, 0, 1.0, {})
test("Blaze boosts Fire at low HP", mult == 1.5, f"mult={mult}")

a2 = create_pokemon("Charizard2", ["Fire", "Flying"], "Blaze")
a2.current_hp = a2.max_hp  # full HP
_, mult2, _ = AbilityHandler.modify_outgoing_damage(a2, create_pokemon("D", ["Normal"], None), make_move("Flamethrower", "Fire", 90, "Special"), 90, 0, 1.0, {})
test("Blaze no boost at full HP", mult2 == 1.0, f"mult={mult2}")

# -- Defeatist --
a = create_pokemon("Archeops", ["Rock", "Flying"], "Defeatist")
a.current_hp = a.max_hp // 2  # exactly half
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Rock Slide", "Rock", 75), 75, 0, 1.0, {})
test("Defeatist halves damage at <=50% HP", mult == 0.5, f"mult={mult}")

# -- Sand Force --
a = create_pokemon("Excadrill", ["Ground", "Steel"], "Sand Force")
bs = {'weather': {'type': 'Sandstorm', 'turns_remaining': 5}}
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None), make_move("Earthquake", "Ground", 100), 100, 0, 1.0, bs)
test("Sand Force 1.3x in Sandstorm for Ground", mult == 1.3, f"mult={mult}")

# -- Sheer Force --
a = create_pokemon("Nidoking", ["Poison", "Ground"], "Sheer Force")
eff = [{'effect_type': 'STATUS', 'probability': 30, 'status_condition': 'Poison'}]
_, mult, _ = AbilityHandler.modify_outgoing_damage(a, create_pokemon("D", ["Normal"], None),
    make_move("Sludge Bomb", "Poison", 90, "Special", effects=eff), 90, 0, 1.0, {})
test("Sheer Force 1.3x with secondary effect", mult == 1.3, f"mult={mult}")


# ============================================================
# 3. DEFENDER DAMAGE ABILITIES
# ============================================================
section("Defender Damage Reduction")

a = create_pokemon("A", ["Normal"], None)

# -- Thick Fat --
d = create_pokemon("Snorlax", ["Normal"], "Thick Fat")
mult = AbilityHandler.modify_incoming_damage(a, d, make_move("Flamethrower", "Fire", 90, "Special"), 100, 1.0, {})
test("Thick Fat halves Fire", mult == 0.5, f"mult={mult}")
mult2 = AbilityHandler.modify_incoming_damage(a, d, make_move("Ice Beam", "Ice", 90, "Special"), 100, 1.0, {})
test("Thick Fat halves Ice", mult2 == 0.5, f"mult={mult2}")

# -- Filter / Solid Rock --
d = create_pokemon("Golem", ["Rock", "Ground"], "Solid Rock")
mult = AbilityHandler.modify_incoming_damage(a, d, make_move("Surf", "Water", 90, "Special"), 100, 4.0, {})
test("Solid Rock reduces SE damage", mult == 0.75, f"mult={mult}")

# -- Multiscale --
d = create_pokemon("Dragonite", ["Dragon", "Flying"], "Multiscale")
d.current_hp = d.max_hp  # full HP
mult = AbilityHandler.modify_incoming_damage(a, d, make_move("Ice Beam", "Ice", 90, "Special"), 100, 4.0, {})
test("Multiscale halves at full HP", mult == 0.5, f"mult={mult}")

d2 = create_pokemon("Dragonite2", ["Dragon", "Flying"], "Multiscale")
d2.current_hp = d2.max_hp - 1  # not full
mult2 = AbilityHandler.modify_incoming_damage(a, d2, make_move("Ice Beam", "Ice", 90, "Special"), 100, 4.0, {})
test("Multiscale no effect below full", mult2 == 1.0, f"mult={mult2}")

# -- Fur Coat --
d = create_pokemon("Furfrou", ["Normal"], "Fur Coat")
mult = AbilityHandler.modify_incoming_damage(a, d, make_move("Return", "Normal", 102), 100, 1.0, {})
test("Fur Coat halves physical", mult == 0.5, f"mult={mult}")

# -- Ice Scales --
d = create_pokemon("Frosmoth", ["Ice", "Bug"], "Ice Scales")
mult = AbilityHandler.modify_incoming_damage(a, d, make_move("Flamethrower", "Fire", 90, "Special"), 100, 2.0, {})
test("Ice Scales halves special", mult == 0.5, f"mult={mult}")

# -- Heatproof --
d = create_pokemon("Bronzong", ["Steel", "Psychic"], "Heatproof")
mult = AbilityHandler.modify_incoming_damage(a, d, make_move("Flamethrower", "Fire", 90, "Special"), 100, 2.0, {})
test("Heatproof halves Fire", mult == 0.5, f"mult={mult}")

# -- Fluffy (contact half / fire double) --
d = create_pokemon("Bewear", ["Normal", "Fighting"], "Fluffy")
mult_c = AbilityHandler.modify_incoming_damage(a, d, make_move("Return", "Normal", 102), 100, 1.0, {}, is_contact=True)
test("Fluffy halves contact", mult_c == 0.5, f"mult={mult_c}")
mult_f = AbilityHandler.modify_incoming_damage(a, d, make_move("Flamethrower", "Fire", 90, "Special"), 100, 1.0, {})
test("Fluffy doubles Fire", mult_f == 2.0, f"mult={mult_f}")

# -- Mold Breaker ignores defensive abilities --
a_mb = create_pokemon("Excadrill", ["Ground", "Steel"], "Mold Breaker")
d_lev = create_pokemon("WashRotom", ["Electric", "Water"], "Levitate")
mult = AbilityHandler.modify_incoming_damage(a_mb, d_lev, make_move("Earthquake", "Ground", 100), 100, 1.0, {})
test("Mold Breaker bypasses defensive abilities", mult == 1.0, f"mult={mult}")


# ============================================================
# 4. STAT CHANGE MODIFICATION (Contrary, Simple, Clear Body, Defiant, Competitive)
# ============================================================
section("Stat Change Modification")

# -- Contrary --
c = AbilityHandler.modify_stat_change(create_pokemon("Serperior", ["Grass"], "Contrary"), 'sp_attack', -2)
test("Contrary inverts -2 â†’ +2", c == 2, f"change={c}")
c2 = AbilityHandler.modify_stat_change(create_pokemon("Serperior", ["Grass"], "Contrary"), 'attack', 1)
test("Contrary inverts +1 â†’ -1", c2 == -1, f"change={c2}")

# -- Simple --
c = AbilityHandler.modify_stat_change(create_pokemon("Bidoof", ["Normal"], "Simple"), 'attack', 1)
test("Simple doubles +1 â†’ +2", c == 2, f"change={c}")
c2 = AbilityHandler.modify_stat_change(create_pokemon("Bidoof", ["Normal"], "Simple"), 'defense', -1)
test("Simple doubles -1 â†’ -2", c2 == -2, f"change={c2}")

# -- Clear Body --
blocked, counter = AbilityHandler.check_stat_drop_immunity(
    create_pokemon("Metagross", ["Steel", "Psychic"], "Clear Body"), 'attack', -1)
test("Clear Body blocks all stat drops", blocked)
test("Clear Body has no counter boost", counter is None)

# -- White Smoke --
blocked, counter = AbilityHandler.check_stat_drop_immunity(
    create_pokemon("Torkoal", ["Fire"], "White Smoke"), 'speed', -1)
test("White Smoke blocks stat drops", blocked)

# -- Hyper Cutter (only protects Attack) --
blocked, _ = AbilityHandler.check_stat_drop_immunity(
    create_pokemon("Kingler", ["Water"], "Hyper Cutter"), 'attack', -1)
test("Hyper Cutter blocks Attack drop", blocked)
not_blocked, _ = AbilityHandler.check_stat_drop_immunity(
    create_pokemon("Kingler", ["Water"], "Hyper Cutter"), 'defense', -1)
test("Hyper Cutter does NOT block Defense drop", not not_blocked)

# -- Defiant --
blocked, counter = AbilityHandler.check_stat_drop_immunity(
    create_pokemon("Braviary", ["Normal", "Flying"], "Defiant"), 'defense', -1)
test("Defiant does not block the drop", not blocked)
test("Defiant counter-boosts Attack +2", counter == ('attack', 2), f"counter={counter}")

# -- Competitive --
blocked, counter = AbilityHandler.check_stat_drop_immunity(
    create_pokemon("Milotic", ["Water"], "Competitive"), 'sp_defense', -1)
test("Competitive does not block the drop", not blocked)
test("Competitive counter-boosts SpAtk +2", counter == ('sp_attack', 2), f"counter={counter}")

# -- Stat increase does NOT trigger Clear Body --
blocked, _ = AbilityHandler.check_stat_drop_immunity(
    create_pokemon("Metagross", ["Steel", "Psychic"], "Clear Body"), 'attack', 1)
test("Clear Body ignores stat increases", not blocked)


# ============================================================
# 5. STATUS IMMUNITY
# ============================================================
section("Status Immunity Abilities")

test("Immunity blocks poison", AbilityHandler.check_status_immunity(
    create_pokemon("Snorlax", ["Normal"], "Immunity"), 'poison'))
test("Immunity blocks badly_poison", AbilityHandler.check_status_immunity(
    create_pokemon("Snorlax", ["Normal"], "Immunity"), 'badly_poison'))
test("Immunity allows burn", not AbilityHandler.check_status_immunity(
    create_pokemon("Snorlax", ["Normal"], "Immunity"), 'burn'))

test("Limber blocks paralysis", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Normal"], "Limber"), 'paralysis'))

test("Insomnia blocks sleep", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Normal"], "Insomnia"), 'sleep'))
test("Vital Spirit blocks sleep", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Normal"], "Vital Spirit"), 'sleep'))

test("Water Veil blocks burn", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Water"], "Water Veil"), 'burn'))

test("Magma Armor blocks freeze", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Fire"], "Magma Armor"), 'freeze'))

test("Own Tempo blocks confusion", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Normal"], "Own Tempo"), 'confusion'))

test("Comatose blocks everything", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Normal"], "Comatose"), 'burn'))

# -- Leaf Guard (conditional on Sun) --
test("Leaf Guard blocks in Sun", AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Grass"], "Leaf Guard"), 'paralysis',
    {'weather': {'type': 'Sun', 'turns_remaining': 5}}))
test("Leaf Guard fails without Sun", not AbilityHandler.check_status_immunity(
    create_pokemon("P", ["Grass"], "Leaf Guard"), 'paralysis',
    {'weather': {'type': 'Rain', 'turns_remaining': 5}}))


# ============================================================
# 6. CONTACT ABILITIES
# ============================================================
section("Contact Abilities (Defender triggers)")

# Multiple seeds to find one where Static fires
triggered_static = False
for seed in range(50):
    random.seed(seed)
    a = create_pokemon("Attacker", ["Normal"], None)
    d = create_pokemon("Pikachu", ["Electric"], "Static")
    AbilityHandler.on_contact(a, d, make_move("Tackle", "Normal", 40), lambda m: None, {})
    if a.status == 'paralysis':
        triggered_static = True
        break
test("Static can inflict paralysis on contact", triggered_static)

triggered_flamebody = False
for seed in range(50):
    random.seed(seed)
    a = create_pokemon("Attacker", ["Normal"], None)
    d = create_pokemon("Magcargo", ["Fire", "Rock"], "Flame Body")
    AbilityHandler.on_contact(a, d, make_move("Tackle", "Normal", 40), lambda m: None, {})
    if a.status == 'burn':
        triggered_flamebody = True
        break
test("Flame Body can inflict burn on contact", triggered_flamebody)

# -- Rough Skin --
a = create_pokemon("Attacker", ["Normal"], None)
d = create_pokemon("Garchomp", ["Dragon", "Ground"], "Rough Skin")
initial_hp = a.current_hp
AbilityHandler.on_contact(a, d, make_move("Tackle", "Normal", 40), lambda m: None, {})
test("Rough Skin deals recoil to attacker", a.current_hp < initial_hp, f"hp={a.current_hp}")

# -- Iron Barbs --
a = create_pokemon("Attacker", ["Normal"], None)
d = create_pokemon("Ferrothorn", ["Grass", "Steel"], "Iron Barbs")
initial_hp = a.current_hp
AbilityHandler.on_contact(a, d, make_move("Tackle", "Normal", 40), lambda m: None, {})
test("Iron Barbs deals recoil to attacker", a.current_hp < initial_hp, f"hp={a.current_hp}")

# -- Mummy --
a = create_pokemon("Attacker", ["Normal"], "Intimidate")
d = create_pokemon("Cofagrigus", ["Ghost"], "Mummy")
AbilityHandler.on_contact(a, d, make_move("Shadow Claw", "Ghost", 70), lambda m: None, {})
test("Mummy replaces attacker's ability", a.ability == 'Mummy', f"ability={a.ability}")

# -- Gooey / Tangling Hair --
a = create_pokemon("Attacker", ["Normal"], None)
d = create_pokemon("Goodra", ["Dragon"], "Gooey")
AbilityHandler.on_contact(a, d, make_move("Tackle", "Normal", 40), lambda m: None, {})
test("Gooey lowers attacker Speed", a.stat_stages['speed'] == -1, f"stage={a.stat_stages['speed']}")

# -- Non-contact moves don't trigger --
a = create_pokemon("Attacker", ["Normal"], None)
d = create_pokemon("Pikachu", ["Electric"], "Static")
random.seed(0)
AbilityHandler.on_contact(a, d, make_move("Earthquake", "Ground", 100), lambda m: None, {})
test("Non-contact doesn't trigger Static", a.status is None)


# ============================================================
# 7. SWITCH-IN ABILITIES
# ============================================================
section("Switch-In Abilities")

# -- Weather setters --
for ability, weather_type in [('Drought', 'Sun'), ('Drizzle', 'Rain'), ('Sand Stream', 'Sandstorm'), ('Snow Warning', 'Hail')]:
    p = create_pokemon(f"P-{ability}", ["Normal"], ability)
    opp = create_pokemon("Opp", ["Normal"], None)
    st = battle_state(p, opp)
    tm = TurnManager(st)
    tm._trigger_switch_in_ability(p)
    test(f"{ability} sets {weather_type}", st['weather']['type'] == weather_type,
         f"weather={st['weather']['type']}")

# -- Intimidate --
p = create_pokemon("Gyarados", ["Water", "Flying"], "Intimidate")
opp = create_pokemon("Pikachu", ["Electric"], None)
st = battle_state(p, opp)
tm = TurnManager(st)
tm._trigger_switch_in_ability(p)
test("Intimidate lowers opponent Attack", opp.stat_stages['attack'] == -1, f"stage={opp.stat_stages['attack']}")

# -- Intimidate vs Clear Body --
p = create_pokemon("Gyarados", ["Water", "Flying"], "Intimidate")
opp = create_pokemon("Metagross", ["Steel", "Psychic"], "Clear Body")
st = battle_state(p, opp)
tm = TurnManager(st)
tm._trigger_switch_in_ability(p)
test("Intimidate blocked by Clear Body", opp.stat_stages['attack'] == 0, f"stage={opp.stat_stages['attack']}")

# -- Intimidate vs Defiant --
p = create_pokemon("Gyarados", ["Water", "Flying"], "Intimidate")
opp = create_pokemon("Braviary", ["Normal", "Flying"], "Defiant")
st = battle_state(p, opp)
tm = TurnManager(st)
tm._trigger_switch_in_ability(p)
# Intimidate: -1 atk, then Defiant: +2 atk => net +1
test("Intimidate + Defiant = net +1 Attack", opp.stat_stages['attack'] == 1, f"stage={opp.stat_stages['attack']}")

# -- Intimidate vs Contrary --
p = create_pokemon("Gyarados", ["Water", "Flying"], "Intimidate")
opp = create_pokemon("Serperior", ["Grass"], "Contrary")
st = battle_state(p, opp)
tm = TurnManager(st)
tm._trigger_switch_in_ability(p)
test("Intimidate + Contrary raises Attack", opp.stat_stages['attack'] == 1, f"stage={opp.stat_stages['attack']}")

# -- Download --
p = create_pokemon("Porygon2", ["Normal"], "Download")
opp = create_pokemon("Opp", ["Normal"], None, stats={'hp': 200, 'attack': 100, 'defense': 80, 'sp_attack': 100, 'sp_defense': 120, 'speed': 100})
st = battle_state(p, opp)
tm = TurnManager(st)
tm._trigger_switch_in_ability(p)
test("Download boosts Attack when Def<SpDef", p.stat_stages['attack'] == 1, f"stage={p.stat_stages['attack']}")

p2 = create_pokemon("Porygon2b", ["Normal"], "Download")
opp2 = create_pokemon("Opp2", ["Normal"], None, stats={'hp': 200, 'attack': 100, 'defense': 120, 'sp_attack': 100, 'sp_defense': 80, 'speed': 100})
st2 = battle_state(p2, opp2)
tm2 = TurnManager(st2)
tm2._trigger_switch_in_ability(p2)
test("Download boosts SpAtk when Def>=SpDef", p2.stat_stages['sp_attack'] == 1, f"stage={p2.stat_stages['sp_attack']}")

# -- Terrain setters --
for ability, terrain_type in [('Electric Surge', 'Electric'), ('Grassy Surge', 'Grassy'),
                               ('Misty Surge', 'Misty'), ('Psychic Surge', 'Psychic')]:
    p = create_pokemon(f"P-{ability}", ["Normal"], ability)
    opp = create_pokemon("Opp", ["Normal"], None)
    st = battle_state(p, opp)
    tm = TurnManager(st)
    tm._trigger_switch_in_ability(p)
    terrain = st.get('field_effects', {}).get('terrain', {}).get('type')
    test(f"{ability} sets {terrain_type} terrain", terrain == terrain_type, f"terrain={terrain}")


# ============================================================
# 8. SWITCH-OUT ABILITIES
# ============================================================
section("Switch-Out Abilities")

# -- Natural Cure --
p = create_pokemon("Chansey", ["Normal"], "Natural Cure")
p.status = 'poison'
AbilityHandler.on_switch_out(p, lambda m: None)
test("Natural Cure cures status on switch", p.status is None, f"status={p.status}")

# -- Natural Cure (no status) --
p2 = create_pokemon("Chansey2", ["Normal"], "Natural Cure")
AbilityHandler.on_switch_out(p2, lambda m: None)
test("Natural Cure no-op without status", p2.status is None)

# -- Regenerator --
p = create_pokemon("Slowbro", ["Water", "Psychic"], "Regenerator")
p.current_hp = 100  # lost 100 HP
AbilityHandler.on_switch_out(p, lambda m: None)
expected_heal = p.max_hp // 3  # 200//3 = 66
test("Regenerator heals 1/3 on switch", p.current_hp == 100 + expected_heal, f"hp={p.current_hp}")


# ============================================================
# 9. SPEED MODIFIERS
# ============================================================
section("Speed Modification")

for ability, weather, expected_mult in [
    ('Swift Swim', 'Rain', 2), ('Chlorophyll', 'Sun', 2),
    ('Sand Rush', 'Sandstorm', 2), ('Slush Rush', 'Hail', 2)]:
    p = create_pokemon(f"P-{ability}", ["Normal"], ability)
    bs = {'weather': {'type': weather, 'turns_remaining': 5}}
    spd = AbilityHandler.modify_speed(p, 100, bs)
    test(f"{ability} doubles in {weather}", spd == 100 * expected_mult, f"speed={spd}")

# Wrong weather â†’ no boost
spd = AbilityHandler.modify_speed(create_pokemon("P", ["Water"], "Swift Swim"), 100,
    {'weather': {'type': 'Sun', 'turns_remaining': 5}})
test("Swift Swim no boost in Sun", spd == 100, f"speed={spd}")

# -- Quick Feet --
p = create_pokemon("Ursaring", ["Normal"], "Quick Feet")
p.status = 'paralysis'
spd = AbilityHandler.modify_speed(p, 100, {'weather': {'type': 'None'}})
test("Quick Feet 1.5x when statused", spd == 150, f"speed={spd}")

# -- Slow Start --
p = create_pokemon("Regigigas", ["Normal"], "Slow Start")
p.turns_active = 0
spd = AbilityHandler.modify_speed(p, 100, {'weather': {'type': 'None'}})
test("Slow Start halves speed first 5 turns", spd == 50, f"speed={spd}")

p2 = create_pokemon("Regigigas2", ["Normal"], "Slow Start")
p2.turns_active = 5
spd2 = AbilityHandler.modify_speed(p2, 100, {'weather': {'type': 'None'}})
test("Slow Start normal after 5 turns", spd2 == 100, f"speed={spd2}")


# ============================================================
# 10. ACCURACY MODIFIERS
# ============================================================
section("Accuracy Modification")

# -- Compound Eyes --
a = create_pokemon("Butterfree", ["Bug", "Flying"], "Compound Eyes")
d = create_pokemon("D", ["Normal"], None)
acc, _ = AbilityHandler.modify_accuracy(a, d, 75, make_move("Sleep Powder", "Grass", 0, "Status"), {})
test("Compound Eyes: 75 â†’ 97", acc == 97, f"acc={acc}")

# -- Hustle --
a = create_pokemon("Durant", ["Bug", "Steel"], "Hustle")
d = create_pokemon("D", ["Normal"], None)
acc, _ = AbilityHandler.modify_accuracy(a, d, 100, make_move("Iron Head", "Steel", 80), {})
test("Hustle reduces Physical accuracy", acc == 80, f"acc={acc}")

# -- No Guard --
a = create_pokemon("Machamp", ["Fighting"], "No Guard")
d = create_pokemon("D", ["Normal"], None)
_, always = AbilityHandler.modify_accuracy(a, d, 70, make_move("Dynamic Punch", "Fighting", 100), {})
test("No Guard always hits", always)

# Defender's No Guard also always hits
a2 = create_pokemon("A", ["Normal"], None)
d2 = create_pokemon("D-NoGuard", ["Normal"], "No Guard")
_, always2 = AbilityHandler.modify_accuracy(a2, d2, 100, make_move("Tackle", "Normal", 40), {})
test("Defender No Guard also always hit", always2)

# -- Sand Veil --
d = create_pokemon("Garchomp", ["Dragon", "Ground"], "Sand Veil")
bs = {'weather': {'type': 'Sandstorm', 'turns_remaining': 5}}
acc, _ = AbilityHandler.modify_accuracy(create_pokemon("A", ["Normal"], None), d, 100, {}, bs)
test("Sand Veil lowers hit chance in Sandstorm", acc == 80, f"acc={acc}")

# -- Snow Cloak --
d = create_pokemon("Froslass", ["Ice", "Ghost"], "Snow Cloak")
bs = {'weather': {'type': 'Hail', 'turns_remaining': 5}}
acc, _ = AbilityHandler.modify_accuracy(create_pokemon("A", ["Normal"], None), d, 100, {}, bs)
test("Snow Cloak lowers hit chance in Hail", acc == 80, f"acc={acc}")


# ============================================================
# 11. CRITICAL HIT MODIFIERS
# ============================================================
section("Critical Hit Modification")

# -- Super Luck --
stage, _ = AbilityHandler.modify_crit_stage(
    create_pokemon("Absol", ["Dark"], "Super Luck"), create_pokemon("D", ["Normal"], None), 0)
test("Super Luck adds +1 crit stage", stage == 1, f"stage={stage}")

# -- Battle Armor --
_, blocked = AbilityHandler.modify_crit_stage(
    create_pokemon("A", ["Normal"], None), create_pokemon("Drapion", ["Poison", "Dark"], "Battle Armor"), 0)
test("Battle Armor blocks crits", blocked)

# -- Shell Armor --
_, blocked = AbilityHandler.modify_crit_stage(
    create_pokemon("A", ["Normal"], None), create_pokemon("Cloyster", ["Water", "Ice"], "Shell Armor"), 0)
test("Shell Armor blocks crits", blocked)

# -- Merciless --
d_poisoned = create_pokemon("D", ["Normal"], None)
d_poisoned.status = 'poison'
stage, _ = AbilityHandler.modify_crit_stage(
    create_pokemon("Toxapex", ["Poison", "Water"], "Merciless"), d_poisoned, 0)
test("Merciless guarantees crit vs poisoned", stage == 3, f"stage={stage}")

# -- Sniper --
crit_mult = AbilityHandler.modify_crit_damage(
    create_pokemon("Kingdra", ["Water", "Dragon"], "Sniper"), 1.5)
test("Sniper boosts crit damage to 2.25", crit_mult == 2.25, f"mult={crit_mult}")


# ============================================================
# 12. WEATHER IMMUNITY
# ============================================================
section("Weather Immunity")

test("Magic Guard immune to Sandstorm", AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Normal"], "Magic Guard"), 'Sandstorm'))
test("Magic Guard immune to Hail", AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Normal"], "Magic Guard"), 'Hail'))
test("Overcoat immune to Sandstorm", AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Normal"], "Overcoat"), 'Sandstorm'))
test("Sand Veil immune to Sandstorm", AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Ground"], "Sand Veil"), 'Sandstorm'))
test("Ice Body immune to Hail", AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Ice"], "Ice Body"), 'Hail'))
test("Snow Cloak immune to Hail", AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Ice"], "Snow Cloak"), 'Hail'))
test("Sand Rush immune to Sandstorm", AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Ground"], "Sand Rush"), 'Sandstorm'))
test("Regular ability NOT immune", not AbilityHandler.check_weather_immunity(
    create_pokemon("P", ["Normal"], "Guts"), 'Sandstorm'))


# ============================================================
# 13. RECOIL IMMUNITY
# ============================================================
section("Recoil Immunity")

test("Rock Head blocks recoil", AbilityHandler.check_recoil_immunity(
    create_pokemon("Rhydon", ["Ground", "Rock"], "Rock Head")))
test("Magic Guard blocks recoil", AbilityHandler.check_recoil_immunity(
    create_pokemon("Clefable", ["Fairy"], "Magic Guard")))
test("No ability = no immunity", not AbilityHandler.check_recoil_immunity(
    create_pokemon("P", ["Normal"], None)))
test("Regular ability = no immunity", not AbilityHandler.check_recoil_immunity(
    create_pokemon("P", ["Normal"], "Intimidate")))


# ============================================================
# 14. FLINCH ABILITIES
# ============================================================
section("Flinch Abilities")

logs = []
prevented = AbilityHandler.on_flinch(
    create_pokemon("Lucario", ["Fighting", "Steel"], "Inner Focus"), lambda m: logs.append(m))
test("Inner Focus prevents flinch", prevented)
test("Inner Focus logs message", len(logs) > 0)

logs = []
p = create_pokemon("Arcanine", ["Fire"], "Steadfast")
prevented = AbilityHandler.on_flinch(p, lambda m: logs.append(m))
test("Steadfast does NOT prevent flinch", not prevented)
test("Steadfast boosts Speed", p.stat_stages['speed'] == 1, f"stage={p.stat_stages['speed']}")


# ============================================================
# 15. CRIT RECEIVED (Anger Point)
# ============================================================
section("Crit Received Abilities")

p = create_pokemon("Tauros", ["Normal"], "Anger Point")
AbilityHandler.on_crit_received(p, lambda m: None)
test("Anger Point maxes Attack on crit", p.stat_stages['attack'] == 6, f"stage={p.stat_stages['attack']}")


# ============================================================
# 16. KO-TRIGGERED ABILITIES
# ============================================================
section("KO-Triggered Abilities")

# -- Moxie --
p = create_pokemon("Salamence", ["Dragon", "Flying"], "Moxie")
AbilityHandler.on_ko(p, lambda m: None)
test("Moxie +1 Attack on KO", p.stat_stages['attack'] == 1)

# Stacking
AbilityHandler.on_ko(p, lambda m: None)
test("Moxie stacks (+2 after 2 KOs)", p.stat_stages['attack'] == 2)

# -- Beast Boost (highest stat) --
p = create_pokemon("Pheromosa", ["Bug", "Fighting"], "Beast Boost",
    stats={'hp': 200, 'attack': 80, 'defense': 80, 'sp_attack': 80, 'sp_defense': 80, 'speed': 150})
AbilityHandler.on_ko(p, lambda m: None)
test("Beast Boost raises highest stat (Speed)", p.stat_stages['speed'] == 1, f"stage={p.stat_stages['speed']}")

# -- Soul-Heart --
p = create_pokemon("Magearna", ["Steel", "Fairy"], "Soul-Heart")
AbilityHandler.on_ko(p, lambda m: None)
test("Soul-Heart +1 SpAtk on KO", p.stat_stages['sp_attack'] == 1)


# ============================================================
# 17. SPECIAL MECHANICS
# ============================================================
section("Special Mechanics (Sturdy, Disguise, Magic Bounce, Protean, Unaware, Adaptability)")

# -- Sturdy --
p = create_pokemon("Golem", ["Rock", "Ground"], "Sturdy")
p.current_hp = p.max_hp  # Full HP
dmg = AbilityHandler.check_sturdy(p, 999, lambda m: None)
test("Sturdy caps lethal at full HP", dmg == p.max_hp - 1, f"dmg={dmg}")

p2 = create_pokemon("Golem2", ["Rock", "Ground"], "Sturdy")
p2.current_hp = p2.max_hp - 1  # Not full
dmg2 = AbilityHandler.check_sturdy(p2, 999, lambda m: None)
test("Sturdy does NOT activate below full HP", dmg2 == 999, f"dmg={dmg2}")

# -- Disguise --
p = create_pokemon("Mimikyu", ["Ghost", "Fairy"], "Disguise")
p.disguise_broken = False
blocked = AbilityHandler.check_disguise(p, {}, lambda m: None)
test("Disguise blocks first hit", blocked)
test("Disguise breaks after", p.disguise_broken)

blocked2 = AbilityHandler.check_disguise(p, {}, lambda m: None)
test("Disguise doesn't block second hit", not blocked2)

# -- Magic Bounce --
d = create_pokemon("Espeon", ["Psychic"], "Magic Bounce")
reflected = AbilityHandler.check_magic_bounce(d, make_move("Stealth Rock", "Rock", 0, "Status", causes_damage=False), lambda m: None)
test("Magic Bounce reflects status moves", reflected)

not_reflected = AbilityHandler.check_magic_bounce(d, make_move("Thunderbolt", "Electric", 90, "Special"), lambda m: None)
test("Magic Bounce ignores damaging moves", not not_reflected)

# -- Protean --
a = create_pokemon("Greninja", ["Water", "Dark"], "Protean")
AbilityHandler.on_before_move(a, make_move("Ice Beam", "Ice", 90, "Special"), {}, lambda m: None)
test("Protean changes type to move type", a.type1 == "Ice", f"type1={a.type1}")
test("Protean removes secondary type", a.type2 is None, f"type2={a.type2}")

# -- Unaware --
ign_atk, ign_def = AbilityHandler.check_unaware(
    create_pokemon("Clefable", ["Fairy"], "Unaware"),
    create_pokemon("D", ["Normal"], None), {})
test("Unaware(attacker) ignores defender boosts", ign_def)
test("Unaware(attacker) doesn't ignore own boosts", not ign_atk)

ign_atk2, ign_def2 = AbilityHandler.check_unaware(
    create_pokemon("A", ["Normal"], None),
    create_pokemon("Quagsire", ["Water", "Ground"], "Unaware"), {})
test("Unaware(defender) ignores attacker boosts", ign_atk2)
test("Unaware(defender) doesn't ignore own boosts", not ign_def2)

# -- Adaptability --
stab = AbilityHandler.modify_stab(create_pokemon("Porygon-Z", ["Normal"], "Adaptability"), 1.5)
test("Adaptability gives 2.0 STAB", stab == 2.0, f"stab={stab}")

stab_normal = AbilityHandler.modify_stab(create_pokemon("P", ["Normal"], "Intimidate"), 1.5)
test("Normal ability keeps 1.5 STAB", stab_normal == 1.5, f"stab={stab_normal}")

# -- Skill Link --
hits = AbilityHandler.modify_multi_hit(create_pokemon("Cloyster", ["Water", "Ice"], "Skill Link"), 3)
test("Skill Link maxes multi-hit to 5", hits == 5, f"hits={hits}")

# -- Parental Bond --
hits = AbilityHandler.modify_multi_hit(create_pokemon("Kangaskhan", ["Normal"], "Parental Bond"), 1)
test("Parental Bond makes single-hit â†’ 2", hits == 2, f"hits={hits}")

# -- Flash Fire boost --
p = create_pokemon("Arcanine", ["Fire"], "Flash Fire")
p.flash_fire_active = True
boost = AbilityHandler.get_flash_fire_boost(p)
test("Flash Fire active gives 1.5x Fire", boost == 1.5, f"boost={boost}")

p2 = create_pokemon("Arcanine2", ["Fire"], "Flash Fire")
boost2 = AbilityHandler.get_flash_fire_boost(p2)
test("Flash Fire inactive = 1.0", boost2 == 1.0, f"boost={boost2}")

# -- Mold Breaker --
test("Mold Breaker detection", AbilityHandler.check_mold_breaker(
    create_pokemon("Excadrill", ["Ground", "Steel"], "Mold Breaker")))
test("Turboblaze detection", AbilityHandler.check_mold_breaker(
    create_pokemon("Reshiram", ["Dragon", "Fire"], "Turboblaze")))
test("Teravolt detection", AbilityHandler.check_mold_breaker(
    create_pokemon("Zekrom", ["Dragon", "Electric"], "Teravolt")))
test("Normal ability not Mold Breaker", not AbilityHandler.check_mold_breaker(
    create_pokemon("P", ["Normal"], "Intimidate")))

# -- Type Change (Pixilate, Refrigerate, Aerilate, Galvanize) --
for ability, expected_type in [('Pixilate', 'Fairy'), ('Refrigerate', 'Ice'),
                                 ('Aerilate', 'Flying'), ('Galvanize', 'Electric')]:
    p = create_pokemon(f"P-{ability}", ["Normal"], ability)
    new_type, mult = AbilityHandler.check_type_change(p, make_move("Return", "Normal", 102))
    test(f"{ability} changes Normal â†’ {expected_type}", new_type == expected_type, f"type={new_type}")
    test(f"{ability} gives 1.2x boost", mult == 1.2, f"mult={mult}")

# Non-Normal moves should NOT be changed
p_pix = create_pokemon("P-Pix", ["Normal"], "Pixilate")
new_type, mult = AbilityHandler.check_type_change(p_pix, make_move("Flamethrower", "Fire", 90, "Special"))
test("Pixilate doesn't change non-Normal moves", new_type is None)


# ============================================================
# 18. TRAPPING ABILITIES
# ============================================================
section("Trapping Abilities")

# -- Shadow Tag --
test("Shadow Tag traps", AbilityHandler.check_trapping(
    create_pokemon("Wobbuffet", ["Psychic"], "Shadow Tag"),
    create_pokemon("Pidgey", ["Normal", "Flying"], None), {}, lambda m: None))

# Shadow Tag vs Shadow Tag: no trap
test("Shadow Tag vs Shadow Tag = no trap", not AbilityHandler.check_trapping(
    create_pokemon("Wobb1", ["Psychic"], "Shadow Tag"),
    create_pokemon("Wobb2", ["Psychic"], "Shadow Tag"), {}, lambda m: None))

# -- Arena Trap --
test("Arena Trap traps grounded", AbilityHandler.check_trapping(
    create_pokemon("Dugtrio", ["Ground"], "Arena Trap"),
    create_pokemon("Pikachu", ["Electric"], None), {}, lambda m: None))

# Arena Trap vs Flying: no trap
test("Arena Trap doesn't trap Flying", not AbilityHandler.check_trapping(
    create_pokemon("Dugtrio", ["Ground"], "Arena Trap"),
    create_pokemon("Pidgey", ["Normal", "Flying"], None), {}, lambda m: None))

# Arena Trap vs Levitate: no trap
test("Arena Trap doesn't trap Levitate", not AbilityHandler.check_trapping(
    create_pokemon("Dugtrio", ["Ground"], "Arena Trap"),
    create_pokemon("Rotom", ["Electric", "Ghost"], "Levitate"), {}, lambda m: None))

# -- Magnet Pull --
test("Magnet Pull traps Steel", AbilityHandler.check_trapping(
    create_pokemon("Magnezone", ["Electric", "Steel"], "Magnet Pull"),
    create_pokemon("Skarmory", ["Steel", "Flying"], None), {}, lambda m: None))

test("Magnet Pull doesn't trap non-Steel", not AbilityHandler.check_trapping(
    create_pokemon("Magnezone", ["Electric", "Steel"], "Magnet Pull"),
    create_pokemon("Pikachu", ["Electric"], None), {}, lambda m: None))


# ============================================================
# 19. START-OF-TURN & END-OF-TURN ABILITIES
# ============================================================
section("Start/End of Turn Abilities")

# -- Speed Boost --
p = create_pokemon("Blaziken", ["Fire", "Fighting"], "Speed Boost")
p.turns_active = 1
AbilityHandler.start_of_turn(p, {}, lambda m: None)
test("Speed Boost +1 Speed after turn 1", p.stat_stages['speed'] == 1)

p2 = create_pokemon("Blaziken2", ["Fire", "Fighting"], "Speed Boost")
p2.turns_active = 0
AbilityHandler.start_of_turn(p2, {}, lambda m: None)
test("Speed Boost no boost on turn 0", p2.stat_stages['speed'] == 0)

# -- Poison Heal --
p = create_pokemon("Breloom", ["Grass", "Fighting"], "Poison Heal")
p.status = 'poison'
p.current_hp = 100
AbilityHandler.start_of_turn(p, {}, lambda m: None)
test("Poison Heal restores HP when poisoned", p.current_hp > 100, f"hp={p.current_hp}")

# -- Bad Dreams --
sleeper = create_pokemon("Darkrai", ["Dark"], "Bad Dreams")
victim = create_pokemon("Pikachu", ["Electric"], None)
victim.status = 'sleep'
initial_hp = victim.current_hp
AbilityHandler.end_of_turn(sleeper, {}, lambda m: None, [victim])
test("Bad Dreams damages sleeping opponents", victim.current_hp < initial_hp, f"hp={victim.current_hp}")

# -- Rain Dish --
p = create_pokemon("Tentacruel", ["Water", "Poison"], "Rain Dish")
p.current_hp = 150
bs = {'weather': {'type': 'Rain', 'turns_remaining': 5}}
AbilityHandler.end_of_turn(p, bs, lambda m: None)
test("Rain Dish heals in Rain", p.current_hp > 150, f"hp={p.current_hp}")

# -- Solar Power (sun damage) --
p = create_pokemon("Charizard", ["Fire", "Flying"], "Solar Power")
initial_hp = p.current_hp
bs = {'weather': {'type': 'Sun', 'turns_remaining': 5}}
AbilityHandler.end_of_turn(p, bs, lambda m: None)
test("Solar Power damages in Sun", p.current_hp < initial_hp, f"hp={p.current_hp}")

# -- Dry Skin end-of-turn --
p_rain = create_pokemon("Toxicroak", ["Poison", "Fighting"], "Dry Skin")
p_rain.current_hp = 150
AbilityHandler.end_of_turn(p_rain, {'weather': {'type': 'Rain', 'turns_remaining': 5}}, lambda m: None)
test("Dry Skin heals in Rain", p_rain.current_hp > 150, f"hp={p_rain.current_hp}")

p_sun = create_pokemon("Toxicroak2", ["Poison", "Fighting"], "Dry Skin")
initial_hp = p_sun.current_hp
AbilityHandler.end_of_turn(p_sun, {'weather': {'type': 'Sun', 'turns_remaining': 5}}, lambda m: None)
test("Dry Skin damages in Sun", p_sun.current_hp < initial_hp, f"hp={p_sun.current_hp}")

# -- Moody --
random.seed(99)
p = create_pokemon("Octillery", ["Water"], "Moody")
AbilityHandler.end_of_turn(p, {}, lambda m: None)
total_change = sum(p.stat_stages[s] for s in ['attack', 'defense', 'sp_attack', 'sp_defense', 'speed'])
test("Moody changes stats (net +1)", total_change == 1, f"total={total_change}")

# -- Shed Skin --
cured_any = False
for seed in range(100):
    random.seed(seed)
    p = create_pokemon("Scrafty", ["Dark", "Fighting"], "Shed Skin")
    p.status = 'paralysis'
    AbilityHandler.start_of_turn(p, {}, lambda m: None)
    if p.status is None:
        cured_any = True
        break
test("Shed Skin can cure status", cured_any)

# -- Hydration --
p = create_pokemon("Vaporeon", ["Water"], "Hydration")
p.status = 'burn'
AbilityHandler.start_of_turn(p, {'weather': {'type': 'Rain', 'turns_remaining': 5}}, lambda m: None)
test("Hydration cures status in Rain", p.status is None, f"status={p.status}")

p2 = create_pokemon("Vaporeon2", ["Water"], "Hydration")
p2.status = 'burn'
AbilityHandler.start_of_turn(p2, {'weather': {'type': 'Sun', 'turns_remaining': 5}}, lambda m: None)
test("Hydration no effect outside Rain", p2.status == 'burn')


# ============================================================
# 20. AFTER-ATTACKING ABILITIES
# ============================================================
section("After-Attacking Abilities")

# -- Poison Touch --
triggered = False
for seed in range(100):
    random.seed(seed)
    a = create_pokemon("Muk", ["Poison"], "Poison Touch")
    d = create_pokemon("Pidgey", ["Normal", "Flying"], None)
    AbilityHandler.on_after_attacking(a, d, make_move("Poison Jab", "Poison", 80), 50, lambda m: None)
    if d.status == 'poison':
        triggered = True
        break
test("Poison Touch can poison on contact", triggered)


# ============================================================
# 21. FULL TURN INTEGRATION TESTS
# ============================================================
section("Full Turn Integration (execute_turn)")

# Test: Levitate user doesn't take Earthquake damage through full turn
random.seed(42)
a = create_pokemon("Garchomp", ["Dragon", "Ground"], None, stats={'hp': 200, 'attack': 130, 'defense': 100, 'sp_attack': 80, 'sp_defense': 100, 'speed': 102})
d = create_pokemon("Rotom-W", ["Electric", "Water"], "Levitate", stats={'hp': 200, 'attack': 65, 'defense': 107, 'sp_attack': 105, 'sp_defense': 107, 'speed': 86})
st = battle_state(a, d)
tm = TurnManager(st)

action_a = BattleAction(a, ActionType.FIGHT, move=make_move("Earthquake", "Ground", 100))
action_d = BattleAction(d, ActionType.FIGHT, move=make_move("Hydro Pump", "Water", 110, "Special"))

result = tm.execute_turn([action_a, action_d])
log_text = " ".join(result['turn_log'])
test("Levitate immunity in full turn", "immune" in log_text.lower() or d.current_hp == d.max_hp,
     f"hp={d.current_hp}, log={'Levitate' in log_text}")

# Test: Intimidate fires on switch in full battle
random.seed(42)
p = create_pokemon("Gyarados", ["Water", "Flying"], "Intimidate",
    stats={'hp': 200, 'attack': 125, 'defense': 79, 'sp_attack': 60, 'sp_defense': 100, 'speed': 81})
opp = create_pokemon("Pikachu", ["Electric"], "Static",
    stats={'hp': 100, 'attack': 55, 'defense': 40, 'sp_attack': 50, 'sp_defense': 50, 'speed': 90})
new_poke = create_pokemon("Starmie", ["Water", "Psychic"], "Intimidate",
    stats={'hp': 200, 'attack': 75, 'defense': 85, 'sp_attack': 100, 'sp_defense': 85, 'speed': 115})
st = battle_state(p, opp)
st['player1_team'] = [p, new_poke]
tm = TurnManager(st)
# Trigger switch-in for Gyarados at battle start
tm._trigger_switch_in_ability(p)
test("Intimidate integration: opponent Attack drops", opp.stat_stages['attack'] == -1)

# Test: Weather setter + weather damage immunity integration
random.seed(42)
tyranitar = create_pokemon("Tyranitar", ["Rock", "Dark"], "Sand Stream",
    stats={'hp': 200, 'attack': 134, 'defense': 110, 'sp_attack': 95, 'sp_defense': 100, 'speed': 61})
excadrill = create_pokemon("Excadrill", ["Ground", "Steel"], "Sand Rush",
    stats={'hp': 200, 'attack': 135, 'defense': 60, 'sp_attack': 50, 'sp_defense': 65, 'speed': 88})
st = battle_state(tyranitar, excadrill)
tm = TurnManager(st)
tm._trigger_switch_in_ability(tyranitar)
test("Sand Stream + Sandstorm set", st['weather']['type'] == 'Sandstorm')
# Neither should take sandstorm damage (Rock type + Steel type both immune)
initial_hp_t = tyranitar.current_hp
initial_hp_e = excadrill.current_hp
tm._apply_sandstorm_damage()
test("Rock type immune to Sandstorm", tyranitar.current_hp == initial_hp_t)
test("Steel type immune to Sandstorm", excadrill.current_hp == initial_hp_e)


# ============================================================
# RESULTS
# ============================================================
print(f"\n{'='*60}")
print(f"  FINAL RESULTS: {_passed}/{_passed + _failed} tests passed")
if _failed > 0:
    print(f"  {_failed} test(s) FAILED")
else:
    print(f"  ALL TESTS PASSED!")
print(f"{'='*60}")

sys.exit(1 if _failed > 0 else 0)

