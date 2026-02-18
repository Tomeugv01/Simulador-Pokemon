# Comprehensive Codebase Audit Report

**Project:** Simulador-Pokemon (Pokémon Battle Simulator)  
**Date:** Auto-generated audit  
**Scope:** 15 files across `models/`, `src/`, and root `main.py`  
**Policy:** Research only — no files modified  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Per-File Reports](#2-per-file-reports)
3. [Cross-File Dependency Map](#3-cross-file-dependency-map)
4. [Duplicate / Redundant Code](#4-duplicate--redundant-code)
5. [Dead Code & Stubs](#5-dead-code--stubs)
6. [Inconsistencies & Bugs](#6-inconsistencies--bugs)
7. [Broken References & Missing Files](#7-broken-references--missing-files)
8. [Temp / Utility Scripts](#8-temp--utility-scripts)
9. [Master Issue Catalog](#9-master-issue-catalog)

---

## 1. Architecture Overview

### Entry Points
The project has **two completely separate entry points** that serve different purposes:

| Entry Point | File | Purpose |
|---|---|---|
| **Actual Game** | `main.py` (root, 833 lines) | Roguelike Pokémon battle simulator — `PokemonGame` class |
| **Move Browser** | `src/run.py` → `src/main.py` | CLI tool to browse the move database |

### Data Flow
```
Database Layer:       src/database.py (DatabaseManager) → data/pokemon_battle.db
                      src/add_pokemon_data.py (PokemonDataManager)
Repository Layer:     src/repositories.py (PokemonRepository, MoveRepository, EffectRepository)
Model Layer:          models/Pokemon.py, Move.py, Move_efffect.py, experience.py, ability.py
Logic Layer:          models/turn_logic.py (TurnManager), models/cpu.py (CPUTrainer)
Generation Layer:     models/team_generation.py (TeamGenerator)
Game Layer:           main.py (PokemonGame) — orchestrates everything
```

### Database Schema (SQLite)
Tables: `types`, `pokemon`, `moves`, `move_effects`, `move_effect_instances`, `pokemon_learnsets`, `pokemon_evolutions`, `abilities`, `pokemon_abilities`

---

## 2. Per-File Reports

---

### 2.1 `models/__init__.py` (10 lines)

**Purpose:** Package initializer. Exports `Pokemon` and `Move` classes.

**Exports:**
```python
from .Pokemon import Pokemon
from .Move import Move
__all__ = ['Pokemon', 'Move']
```

**Issues:**
- **Incomplete exports:** Does not export `MoveEffect`, `ExperienceCurve`, `TeamGenerator`, `CPUTrainer`, `AbilityHandler`, `TurnManager`, or any enums (`ActionType`, `BattleAction`). Every consumer must import these directly from their submodules.

---

### 2.2 `models/Pokemon.py` (1,159 lines)

**Purpose:** Core `Pokemon` class — stats, HP, status conditions, IVs, EVs, moves, evolution, experience, transformation, substitutes, and volatile conditions.

**Class: `Pokemon`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | 1-80 | Constructs from DB data dict; generates IVs, calculates stats, loads moves and ability |
| `generate_ivs` | ~80-95 | Random 0-31 IVs for each stat |
| `get_type_name` | ~95-115 | Converts type ID → name via `TYPE_NAMES` dict |
| `_load_ability` | ~115-170 | Queries DB for abilities; picks one randomly |
| `_calculate_hp_stat` | ~170-185 | HP stat formula with Shedinja check |
| `_calculate_stat` | ~185-200 | Non-HP stat formula using base stats + IVs |
| `get_effective_stat` | ~200-240 | Applies stat stage multipliers |
| `modify_stat_stage` | ~240-270 | Modifies stat stages with clamping to ±6 |
| `take_damage` | ~270-310 | Handles substitute, HP reduction, faint |
| `heal` | ~310-330 | HP restoration |
| `apply_status` | ~330-375 | Status condition application with type immunities |
| `cure_status` | ~375-395 | Clears status |
| `create_substitute` | ~395-425 | Creates substitute (25% HP cost) |
| `damage_substitute` | ~425-445 | Damages active substitute |
| `can_use_move` | ~445-475 | PP check, disabled check |
| `transform` | ~475-540 | Transform into target (Ditto mechanic) |
| `reset_transform` | ~540-560 | Undo transform |
| `reset_volatile_conditions` | ~560-600 | Clears volatile status on switch-out |
| `process_end_of_turn_effects` | ~600-680 | Burn/poison/toxic/leech seed/nightmare/trap/ingrain |
| `can_move` | ~680-760 | Sleep/freeze/paralysis/confusion/flinch/attraction checks |
| `gain_exp` | ~760-830 | EXP gain + auto level-up |
| `check_moves_learned_at_level` | ~830-870 | Queries DB for moves learned at level |
| `learn_move` | ~870-935 | Learn or replace a move |
| `level_up` | ~935-990 | Recalculates all stats on level-up |
| `can_evolve` | ~990-1040 | Checks evolution availability |
| `evolve` | ~1040-1159 | Performs evolution — loads new data, recalculates stats |

**Standalone Data:**
- `TYPE_NAMES` dict (lines 8-17) — maps type IDs to names

**Issues:**
1. **`TYPE_NAMES` dict duplicated** in `Move.py`, `team_generation.py`, root `main.py` (as `type_map` / `_get_type_name`)
2. **Triple-nested try/except imports** (lines 13-33) — fragile `sys.path` manipulation
3. **`import random` inside methods** — imported at module level AND inside `_load_ability`, `generate_ivs`, etc.
4. **`can_evolve()` uses raw `sqlite3`** (line ~990-1010) — bypasses the repository pattern entirely, opens its own DB connection
5. **`process_end_of_turn_effects()`** duplicates logic that exists in `TurnManager._phase_end_turn()`
6. **`can_move()`** duplicates status checks from `TurnManager._can_use_move()`
7. **Move objects accessed as both objects AND dicts** — `m.get('id')` works because `Move.__getitem__` exists, but this is confusing

---

### 2.3 `models/Move.py` (~170 lines)

**Purpose:** `Move` class with PP management, effect querying, and dict-style access compatibility.

**Class: `Move`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | ~20-65 | Constructs from DB tuple; stores all move attributes |
| `use` | ~65-75 | Decrements PP |
| `restore_pp` | ~75-85 | Restores PP |
| `get_effects` | ~85-120 | Queries DB for move effects |
| `__getitem__` | ~120-135 | Dict-style access (`move['name']`) |
| `get` | ~135-145 | Dict-style `.get()` with default |
| `__contains__` | ~145-150 | `'key' in move` support |
| `__repr__` | ~150-160 | String representation |

**Standalone Data:**
- `TYPE_NAMES` dict (lines 8-17) — **DUPLICATE** of `Pokemon.py`'s dict

**Issues:**
1. **`TYPE_NAMES` dict is an exact copy** from `Pokemon.py` — both files define the same 18-type mapping
2. **`get_effects()` opens raw DB connections** — each call queries `move_effect_instances` JOIN `move_effects` independently
3. **Dict-style access pattern** (`__getitem__`, `get`, `__contains__`) creates confusion about whether `Move` instances are objects or dicts

---

### 2.4 `models/Move_efffect.py` (1,149 lines)

**Purpose:** Move effect system — defines effect types, targets, triggers, and a class hierarchy for applying effects in battle.

**⚠️ Filename has a typo: triple 'f' in "efffect"**

**Enums:**
- `EffectType` — 9 values: STATUS, STAT_CHANGE, HEAL, RECOIL, WEATHER, FIELD, OTHER, SPECIAL, DAMAGE_MODIFIER
- `EffectTarget` — 5 values: SELF, OPPONENT, FIELD, BOTH, ALL
- `TriggerCondition` — 4 values: ON_HIT, ON_USE, ALWAYS, AFTER_DAMAGE

**Class Hierarchy:**

| Class | Parent | Lines | Purpose |
|---|---|---|---|
| `MoveEffect` | — | ~80-200 | Base effect class with `apply()` |
| `StatusEffect` | `MoveEffect` | ~200-280 | Burns, paralysis, sleep, etc. |
| `StatChangeEffect` | `MoveEffect` | ~280-360 | Stat stage modifications |
| `HealEffect` | `MoveEffect` | ~360-440 | HP recovery |
| `RecoilEffect` | `MoveEffect` | ~440-520 | Recoil damage |
| `WeatherEffect` | `MoveEffect` | ~520-600 | Weather setting |
| `FieldEffect` | `MoveEffect` | ~600-680 | Entry hazards, screens, etc. |
| `SpecialEffect` | `MoveEffect` | ~680-950 | **~200-line if/elif chain** for special mechanics |
| `DamageModifierEffect` | `MoveEffect` | ~950-1020 | Damage multipliers |

**Factory Functions:**
- `create_effect_from_data(effect_data)` — creates appropriate subclass from DB data
- `apply_move_effects(move, attacker, defender, ...)` — orchestrates effect application

**Issues:**
1. **Filename typo:** `Move_efffect.py` (triple 'f') — every import referencing this file must use the misspelled name
2. **`SpecialEffect.apply()` is a ~200-line if/elif chain** (lines ~700-950) — handles Protect, Substitute, hazards, screens, weather-dependent healing, status-dependent damage, Psych Up, Disable, Encore, Taunt, Trick Room, etc. Should be decomposed
3. **`__main__` test block** at end of file — prints effect type information
4. **Some effects not fully implemented** — fall through to `pass` or print debug messages

---

### 2.5 `models/cpu.py` (603 lines)

**Purpose:** CPU AI trainer with flag-based scoring for intelligent move selection.

**Enums:**
- `AIFlag` — 17 flags: BASIC, SETUP, STATUS_LOVER, AGGRESSIVE, etc.

**Class: `CPUTrainer`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | ~40-80 | Creates repos, sets AI flags, difficulty, team |
| `choose_move` | ~80-150 | Main move selection logic — calculates scores |
| `_try_switch` | ~150-200 | Evaluates switch opportunities |
| `_calculate_move_score` | ~200-350 | Detailed scoring based on AI flags |
| `_evaluate_type_advantage` | ~350-400 | Scores move type vs opponent |
| `_get_type_effectiveness` | ~400-480 | **Partial type chart** — 8 types only |
| `_check_type_immunity` | ~480-520 | Ground/Normal/Ghost/Fighting immunity checks |
| `_prefer_stab` | ~520-540 | STAB bonus scoring |
| `_prefer_status_moves` | ~540-570 | Status move scoring |
| `_select_from_scores` | ~570-603 | Probabilistic selection from scored moves |

**Issues:**
1. **Partial type effectiveness chart** in `_get_type_effectiveness()` (lines ~400-480) — only covers 8 types (Normal, Fire, Water, Electric, Grass, Ice, Fighting, Ground). The full chart exists in `turn_logic.py`
2. **Creates new `PokemonRepository` and `MoveRepository` per instance** — each CPUTrainer opens its own DB connections
3. **`__main__` block** — test code at end of file
4. **Never actually switches in-game** — `_try_switch()` exists but root `main.py`'s `battle()` always creates a FIGHT action for CPU (line ~300 in root main.py)

---

### 2.6 `models/experience.py` (242 lines)

**Purpose:** Experience curve calculations — EXP-for-level formulas, EXP gain, and level-from-EXP.

**Class: `ExperienceCurve`** (all static methods)

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `exp_for_level` | ~15-80 | Calculates EXP needed for a level based on growth rate |
| `level_from_exp` | ~80-120 | Determines level from total EXP |
| `calculate_exp_gain` | ~120-180 | Battle EXP gain formula |
| `get_exp_curve` | ~180-210 | Returns growth rate string for a Pokémon |
| `get_growth_rate_display` | ~210-242 | Display name for growth rate |

**Issues:**
1. **`import math` is never used** (line 6) — dead import
2. **`exp_curve == 'medium'` not handled** in `exp_for_level()` — the DB stores 'medium' but the method only handles 'medium_fast', 'medium_slow', 'fast', 'slow', 'erratic', 'fluctuating'. Falls through to `medium_fast` default
3. **`__main__` block** — test/demo code at end

---

### 2.7 `models/team_generation.py` (1,448 lines)

**Purpose:** Roguelike team generation with TSB (Total Stat Budget) scaling, archetype system, and reward system.

**Enums:**
- `TeamComposition` — BALANCED, OFFENSIVE, DEFENSIVE, SPEED, BULKY_OFFENSE
- `RewardChoice` — NEW_POKEMON, MOVE_UPGRADE, STAT_BOOST, EVOLUTION
- `Archetype` — SWEEPER, WALL, TANK, SUPPORT, GLASS_CANNON, PIVOT, REVENGE_KILLER, SETUP_SWEEPER, SPECIAL_WALL, PHYSICAL_WALL, MIXED_ATTACKER, HAZARD_SETTER

**Class: `TeamGenerator`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | ~50-80 | Repository setup |
| `_pokemon_to_data` (class) | ~80-115 | Converts Pokemon object → dict |
| `calculate_tsb` | ~115-150 | Total Stat Budget calculation |
| `determine_archetype` | ~150-220 | Categorizes Pokemon by stat distribution |
| `generate_starter_choices` (class) | ~220-340 | Creates 3 groups of balanced starters |
| `generate_team` | ~340-460 | Generates opponent teams with TSB targets |
| `generate_reward_options` (class) | ~460-520 | Post-battle reward generation |
| `get_filtered_moves_for_learning` | ~520-620 | Filters available moves by power cap and type |
| `teach_move_to_pokemon` | ~620-680 | Teaches a specific move |
| `get_pokemon_by_name` | ~680-710 | Name-based lookup |
| `get_team_summary` (class) | ~710-760 | Team stat overview |
| `calculate_round_target_tsb` | ~760-800 | TSB scaling formula per round |

**Standalone Functions (after class):**
- `example_usage()` (~800-1050) — demo script
- `generate_starter_choices()` (~1050-1200) — **DUPLICATE** of class method with DIFFERENT implementation
- `generate_reward_options()` (~1200-1300) — **DUPLICATE** of class method with DIFFERENT implementation
- `get_team_summary()` (~1300-1370) — **DUPLICATE** of class method with DIFFERENT implementation
- `_pokemon_to_data()` (~1370-1448) — **DUPLICATE** of class method with DIFFERENT implementation

**Issues:**
1. **CRITICAL: 4 methods are defined twice** — as class methods AND as standalone functions after `example_usage()`. The standalone versions have DIFFERENT implementations and reference `species_id` keys that don't exist in the repository data
2. **Standalone duplicates would shadow class methods if imported carelessly** — `from team_generation import generate_starter_choices` would get the standalone version
3. **`example_usage()`** is dead code in production

---

### 2.8 `models/turn_logic.py` (2,448 lines)

**Purpose:** Complete turn resolution engine — pre-turn processing, action execution, damage calculation, move effect application, end-of-turn effects, faint handling & win conditions.

**Enums:**
- `ActionType` — FIGHT, SWITCH, ITEM, RUN
- `PriorityBracket` — SWITCH (highest), PRIORITY_PLUS, NORMAL, PRIORITY_MINUS

**Dataclass:**
- `BattleAction` — type, pokemon, move, target, switch_to, priority

**Class: `TurnManager`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | ~60-100 | Stores battle state, teams, logs, field effects |
| `execute_turn` | ~100-140 | Master turn orchestrator: pre-turn → execute → end → faints |
| `_phase_pre_turn` | ~140-200 | Weather tick, field effect tick, start-of-turn abilities, status |
| `_process_weather_tick` | ~200-240 | Weather turn counter, sandstorm/hail damage |
| `_apply_sandstorm_damage` | ~240-280 | Sandstorm damage per Pokémon |
| `_apply_hail_damage` | ~280-320 | Hail damage per Pokémon |
| `_process_field_effects_tick` | ~320-370 | Terrain/room/hazard turn counters |
| `_process_start_of_turn_abilities` | ~370-400 | Drought/Drizzle/Sand Stream/Snow Warning |
| `_process_start_of_turn_items` | ~400-420 | **Checks `pokemon.status == 'healthy'`** — uses wrong sentinel |
| `_process_status_conditions` | ~420-480 | Sleep counter, freeze thaw |
| `_sort_actions` | ~480-530 | Priority bracket sorting, speed ties |
| `_calculate_effective_speed` | ~530-570 | Speed with Trick Room, paralysis, abilities |
| `_phase_execute_actions` | ~570-630 | Iterates sorted actions, executes each |
| `_execute_switch` | ~630-690 | Switch-out/switch-in with hazards and abilities |
| `_execute_move` | ~690-900 | Core move execution — type checks, accuracy, damage, multi-hit |
| `_can_use_move` | ~900-960 | Sleep/freeze/paralysis/confusion/flinch/disable/taunt checks |
| `_determine_num_hits` | ~960-1000 | Multi-hit move roll (2-5 with distribution) |
| `_is_forced_switch_move` | ~1000-1010 | Whirlwind/Roar/Dragon Tail/Circle Throw check |
| `_is_protected` | ~1010-1050 | Protect/Detect/King's Shield/Baneful Bunker |
| `_accuracy_check` | ~1050-1100 | Accuracy/evasion calculation with abilities |
| `_calculate_damage` | ~1100-1270 | Full damage formula: level, power, stats, STAB, type effectiveness, crit, random roll, abilities, weather, burn, screens, items |
| `_get_type_effectiveness` | ~1270-1350 | **Complete 18×18 type chart** |
| `_apply_move_effects` | ~1350-1400 | Delegates to `_handle_status_move` or `_apply_single_effect` |
| `_get_move_effects` | ~1400-1430 | Queries DB for move effects |
| `_handle_status_move` | ~1430-1470 | Status move wrapper |
| `_apply_single_effect` | ~1470-1530 | Effect type dispatcher |
| `_apply_stat_change_effect` | ~1530-1600 | Stat modification with Contrary/Simple |
| `_apply_status_effect` | ~1600-1680 | Status conditions with type immunities |
| `_apply_heal_effect` | ~1680-1730 | HP recovery, drain, weather-dependent |
| `_apply_weather_effect` | ~1730-1770 | Weather setting |
| `_apply_field_effect` | ~1770-2050 | **~280-line method** — Reflect, Light Screen, Spikes, Stealth Rock, Sticky Web, Toxic Spikes, terrains, Trick Room, Tailwind, Safeguard, Wish, substitutes, hazard removal, Aurora Veil |
| `_set_user_side_effect` | ~2050-2070 | Helper for side-specific effects |
| `_get_opponent_side_key` | ~2070-2090 | Returns opponent side key |
| `_apply_other_effect` | ~2090-2320 | **~230-line method** — trapping, charge turns, recharge, multi-hit, fixed damage, weight damage, counters, destiny bond, self-destruct, switch-out, OHKO |
| `_calculate_confusion_damage` | ~2320-2340 | Confusion self-hit damage |
| `_phase_end_turn` | ~2340-2380 | End-of-turn: abilities, items, volatile effects, turn counters |
| `_process_end_of_turn_abilities` | ~2380-2395 | Delegates to `AbilityHandler.end_of_turn` |
| `_process_end_of_turn_items` | ~2395-2400 | **Empty stub — `pass`** |
| `_process_volatile_effects` | ~2400-2420 | Turn counter decrements for volatile statuses |
| `_decrement_turn_counters` | ~2420-2430 | General turn counter decrement |
| `_phase_handle_faints` | ~2430-2440 | Faint detection |
| `_check_win_condition` | ~2440-2448 | All-fainted check |

**Issues:**
1. **Complete type chart** (lines ~1270-1350) — duplicated in `cpu.py` (partial), `ability.py` `_calc_type_effectiveness()` (complete), and referenced data
2. **`_process_start_of_turn_items()` checks `pokemon.status == 'healthy'`** — but `Pokemon` class uses `None` for no status, not the string `'healthy'`
3. **`_current_user_side` is referenced but never set** — will cause `AttributeError`
4. **`_process_end_of_turn_items()` is an empty stub** — items have no end-of-turn effects
5. **`_apply_field_effect()` is 280 lines** — should be decomposed
6. **`_apply_other_effect()` is 230 lines** — should be decomposed
7. **Reflect stored in BOTH `battle_state['field_effects']` AND side effects** — dual storage creates sync issues

---

### 2.9 `models/ability.py` (1,607 lines)

**Purpose:** Comprehensive ability effect handlers for the battle system. Covers 100+ abilities across all interaction points.

**Class: `AbilityHandler`** (all static methods)

**Classification Dictionaries** (~40-200):
- `SWITCH_IN_ABILITIES`, `ATTACKER_DAMAGE_ABILITIES`, `DEFENDER_DAMAGE_ABILITIES`, `TYPE_IMMUNITY_ABILITIES`, `STATUS_IMMUNITY_ABILITIES`, `STAT_PROTECTION_ABILITIES`, `ON_CONTACT_ABILITIES`, `END_OF_TURN_ABILITIES`, `SPEED_MODIFIER_ABILITIES`, `ACCURACY_ABILITIES`, `CRIT_MODIFIER_ABILITIES`, `ON_STAT_CHANGE_ABILITIES`, `ON_KO_ABILITIES`, `ON_HIT_ATTACKER_ABILITIES`, `PRIORITY_ABILITIES`, `ON_FLINCH_ABILITIES`, `ON_CRIT_RECEIVED_ABILITIES`, `SWITCH_OUT_ABILITIES`, `WEATHER_PASSIVE_ABILITIES`, `RECOIL_ABILITIES`, `TRAPPING_ABILITIES`, `SPECIAL_ABILITIES`

**Move Flag Sets** (~200-260):
- `PUNCH_MOVES`, `BITE_MOVES`, `PULSE_MOVES`, `SOUND_MOVES`, `BALL_BOMB_MOVES`, `CONTACT_OVERRIDE_NO`

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `on_switch_in` | ~260-380 | Intimidate, Drizzle, Drought, Sand Stream, Snow Warning, Electric/Psychic/Grassy/Misty Surge, Dauntless Shield, Intrepid Sword, Download, Trace, Imposter, etc. |
| `on_switch_out` | ~380-400 | Natural Cure, Regenerator |
| `modify_outgoing_damage` | ~400-510 | Tough Claws, Iron Fist, Strong Jaw, Mega Launcher, etc. |
| `modify_incoming_damage` | ~510-600 | Multiscale, Shadow Shield, Thick Fat, Dry Skin, Fluffy, etc. |
| `check_type_immunity` | ~600-650 | Levitate, Lightning Rod, Motor Drive, Storm Drain, etc. |
| `check_status_immunity` | ~650-700 | Vital Spirit, Insomnia, Immunity, Magma Armor, Limber, etc. |
| `check_stat_drop_immunity` | ~700-730 | Clear Body, White Smoke, Full Metal Body, Hyper Cutter, Big Pecks |
| `on_contact` | ~730-800 | Static, Flame Body, Poison Point, Effect Spore, Rough Skin, Iron Barbs, Cute Charm, Mummy, etc. |
| `on_after_attacking` | ~800-830 | Moxie, Beast Boost |
| `on_ko` | ~830-850 | Soul-Heart |
| `start_of_turn` | ~850-870 | Slow Start counter |
| `end_of_turn` | ~870-970 | Speed Boost, Poison Heal, Bad Dreams, Rain Dish, Ice Body, Dry Skin, Solar Power, Moody |
| `modify_speed` | ~970-1020 | Swift Swim, Chlorophyll, Sand Rush, Slush Rush, Quick Feet, Unburden, Slow Start |
| `modify_accuracy` | ~1020-1070 | Compound Eyes, Victory Star, Hustle, No Guard, Sand Veil, Snow Cloak, Tangled Feet |
| `modify_crit_stage` | ~1070-1100 | Super Luck, Merciless, Battle Armor, Shell Armor |
| `modify_crit_damage` | ~1100-1110 | Sniper |
| `check_weather_immunity` | ~1110-1140 | Magic Guard, Overcoat, Sand/Ice immunities |
| `check_recoil_immunity` | ~1140-1160 | Rock Head, Magic Guard |
| `check_indirect_damage_immunity` | ~1160-1180 | Magic Guard |
| `on_flinch` | ~1180-1210 | Inner Focus (prevents), Steadfast (Speed boost) |
| `on_crit_received` | ~1210-1230 | Anger Point (max Attack) |
| `check_sturdy` | ~1230-1250 | Sturdy (OHKO prevention at full HP) |
| `check_disguise` | ~1250-1280 | Disguise (blocks first hit, 1/8 HP recoil Gen 8+) |
| `check_magic_bounce` | ~1280-1300 | Magic Bounce (reflects status moves) |
| `check_trapping` | ~1300-1330 | Shadow Tag, Arena Trap, Magnet Pull |
| `modify_stab` | ~1330-1350 | Adaptability (STAB → 2.0×) |
| `check_burn_attack_reduction` | ~1350-1365 | Guts (ignores burn penalty) |
| `check_type_change` | ~1365-1430 | Normalize, Pixilate, Refrigerate, Aerilate, Galvanize, **Protean/Libero** |
| `check_unaware` | ~1430-1450 | Unaware (ignores stat changes) |
| `modify_multi_hit` | ~1450-1475 | Skill Link (always 5), Parental Bond (always 2) |
| `get_flash_fire_boost` | ~1475-1490 | Flash Fire damage boost |
| `check_mold_breaker` | ~1490-1510 | Mold Breaker, Teravolt, Turboblaze |
| `modify_stat_change` | ~1510-1530 | Contrary (inverts), Simple (doubles) |
| `on_before_move` | ~1530-1570 | **Protean/Libero** type change — DUPLICATED from `check_type_change` |

**Module-Level Helpers** (~1570-1607):
- `_set_terrain(battle_state, terrain, turns, log_func)` — terrain setter
- `_calc_type_effectiveness(atk_type, def_type)` — **ANOTHER complete 18×18 type chart**

**Issues:**
1. **Sucker Punch listed in `PUNCH_MOVES`** (line ~210) — incorrect; Sucker Punch is not a punching move in Pokémon games and should NOT receive Iron Fist boost
2. **Duplicate `'Ice Body'` key** in `WEATHER_PASSIVE_ABILITIES` dict — Python silently uses the last value
3. **`Analytic` ability** in `on_after_attacking` — body is just `pass`, not implemented
4. **Protean/Libero duplicated** — type change logic exists in BOTH `check_type_change()` (~1415-1430) AND `on_before_move()` (~1540-1570) with slightly different implementations
5. **`_calc_type_effectiveness()`** contains a COMPLETE type chart — this is the 3rd or 4th copy in the codebase

---

### 2.10 `src/database.py` (2,146 lines)

**Purpose:** `DatabaseManager` — creates database schema, inserts all static data (types, moves, move effects, effect instances, learnsets, evolutions).

**Class: `DatabaseManager`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | ~15-30 | Sets DB path |
| `ensure_data_directory` | ~30-45 | Creates `data/` dir |
| `get_connection` | ~45-60 | Returns `sqlite3.Connection` |
| `initialize_database` | ~60-90 | Orchestrates all table creation and data insertion |
| `_create_tables` | ~90-190 | CREATE TABLE statements for all 9 tables |
| `_insert_types` | ~190-220 | 18 type records |
| `_insert_move_effects` | ~220-500 | ~120 move effect definitions |
| `_insert_moves` | ~500-900 | **742 moves** (Gen 1-7 + Z-moves + Let's Go) |
| `_insert_move_effect_instances` | ~900-1700 | **Massive effects_map** — hundreds of move-to-effect linkages |
| `_get_effect_id` | ~1700-1710 | Helper to get effect ID by name |
| `_insert_pokemon_learnsets` | ~1710-1730 | Imports from `pokemon_learnsets_export.py` |
| `_insert_pokemon_evolutions` | ~1730-1750 | Imports from `pokemon_evolutions_export.py` |

**Standalone Functions** (~1750-2146):
- `get_move_details(move_id)` — queries move + effects
- `get_all_moves()` — all moves ordered by name
- `search_moves_by_type(move_type)` — filter by type
- `get_pokemon_learnset(pokemon_id, max_level=None)` — learnset query
- `get_moves_at_level(pokemon_id, level)` — moves at specific level
- `get_available_moves_for_level(pokemon_id, current_level, count=4)` — most recent moves

**Issues:**
1. **`_insert_pokemon_learnsets()` and `_insert_pokemon_evolutions()`** are duplicated from `add_pokemon_data.py` — both files import from the same export files and insert into the same tables
2. **Standalone functions create new `DatabaseManager()` instances** each call — wasteful; duplicates `MoveRepository` methods
3. **742 moves + hundreds of effect mappings as hardcoded data** — maintenance burden
4. **`sys.path.insert`** inside methods for import resolution

---

### 2.11 `src/repositories.py` (710 lines)

**Purpose:** Repository pattern — structured database queries for Pokémon, moves, and effects.

**Classes:**

| Class | Lines (approx.) | Key Methods |
|---|---|---|
| `PokemonRepository` | ~20-250 | `get_by_id`, `get_all`, `get_by_type`, `get_by_name`, `get_stats`, `get_by_stat_range`, `get_evolution_info`, `get_evolution_chain` (TODO), `get_learnset`, `get_moves_at_level`, `get_moveset_for_level` |
| `MoveRepository` | ~250-500 | `get_by_id`, `get_all`, `get_by_type`, `get_by_name`, `get_by_category`, `search`, `get_by_stat_change`, `get_by_power_range`, `get_random_moves` |
| `EffectRepository` | ~500-620 | `get_for_move`, `get_by_id`, `get_by_type`, `get_all_effect_types`, `get_moves_with_effect` |

**Convenience Functions** (~620-710):
- `get_pokemon(id)`, `get_move(id)`, `get_effect(move_id)` — create repo instances and query

**Issues:**
1. **`get_evolution_chain()` is a TODO stub** — returns empty list
2. **f-string SQL interpolation** for ORDER BY clause — technically an SQL injection vector (though limited to internal use): `f"ORDER BY {order_by}"` in `PokemonRepository.get_by_stat_range()`
3. **Each method opens and closes its own connection** — no connection pooling or sharing
4. **`__main__` block** — test code at end

---

### 2.12 `src/main.py` (~165 lines)

**Purpose:** CLI move database browser — NOT the battle simulator.

**Functions:**
- `display_move(move)` — prints move details
- `display_move_with_effects(move_id)` — prints move with effect info
- `list_all_moves()` — paginated move listing
- `search_move_by_id()` — ID-based lookup
- `search_move_by_name()` — name-based search (**uses raw `DatabaseManager`**)
- `search_moves_by_type_menu()` — type-filtered search
- `main()` — CLI menu loop

**Issues:**
1. **`search_move_by_name()` creates a raw `DatabaseManager` instance** instead of using `MoveRepository.get_by_name()` — duplicates repository functionality
2. **This is NOT the game** — confusing because the actual game is root `main.py`

---

### 2.13 `src/run.py` (~65 lines)

**Purpose:** Application launcher for the move browser.

**Functions:**
- `initialize_database()` — sets up DB via `DatabaseManager` + `PokemonDataManager`
- `main()` — initializes DB, then calls `src/main.py`'s `main()`

**Issues:**
1. **Launches the move browser, NOT the battle game** — misleading given its generic name
2. **`sys.path` manipulation** at top of file

---

### 2.14 `src/add_pokemon_data.py` (794 lines)

**Purpose:** `PokemonDataManager` — inserts Pokémon data (Gen 1-6), learnsets, evolutions, abilities.

**Class: `PokemonDataManager`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | ~15-25 | Gets DB connection |
| `initialize_pokemon_data` | ~25-50 | Orchestrator — calls all insert methods |
| `_insert_pokemon` | ~50-500 | **Gen 1-4 hardcoded** (IDs 1-493) — inline tuples |
| `_insert_gen5_6_pokemon` | ~500-540 | Imports from `gen5_6_pokemon_export.py`, strips 14th field |
| `_insert_pokemon_learnsets` | ~540-570 | Imports from `pokemon_learnsets_export.py` |
| `_insert_pokemon_evolutions` | ~570-600 | Imports from `pokemon_evolutions_export.py` |
| `_insert_abilities` | ~600-630 | Imports from `abilities_data_export.py` |
| `_insert_pokemon_abilities` | ~630-660 | Imports from `pokemon_abilities_export.py` |

**Standalone Functions** (~660-794):
- `get_all_pokemon()` — creates new `PokemonDataManager`, queries all
- `get_pokemon_by_id(pokemon_id)` — creates new instance per call
- `search_pokemon_by_type(type_name)` — creates new instance per call
- `get_pokemon_by_name(name)` — creates new instance per call
- `main()` — demo/test function

**Issues:**
1. **`_insert_pokemon_learnsets()` and `_insert_pokemon_evolutions()` DUPLICATE** the same methods in `database.py`
2. **Each standalone function creates a new `PokemonDataManager`** — wasteful
3. **`_insert_gen5_6_pokemon` strips 14th field** from import data — undocumented tuple manipulation
4. **All import methods use `try/except ImportError`** with warnings — fails silently if export files are missing
5. **`__main__` block** — test code at end

---

### 2.15 Root `main.py` (833 lines)

**Purpose:** **THE ACTUAL GAME** — `PokemonGame` class implementing the roguelike Pokémon battle simulator. This is what players run.

**Class: `PokemonGame`**

| Method | Lines (approx.) | Purpose |
|---|---|---|
| `__init__` | ~30-55 | Creates `TeamGenerator`, empty team, round counter |
| `start` | ~55-95 | Main game loop: welcome → starters → battle loop → rewards → game over |
| `show_welcome_screen` | ~95-115 | ASCII art welcome |
| `starter_selection` | ~115-200 | 3 groups of starters with TSB/archetype display |
| `show_round_info` | ~200-215 | Round number and team status |
| `generate_opponent` | ~215-240 | Team size scales: `min(3 + round//3, 6)` |
| `battle` | ~240-385 | Full battle loop with turn display, action selection, faint handling |
| `get_player_action` | ~385-415 | Fight/Switch/Forfeit menu |
| `choose_move` | ~415-450 | Move selection with type/power display |
| `choose_switch` | ~450-475 | Pokémon switch menu |
| `force_switch` | ~475-498 | Forced switch after faint |
| `execute_turn` | ~498-520 | Bridges player/CPU actions to `TurnManager` |
| `teach_move_to_team` | ~520-600 | Interactive move teaching |
| `offer_rewards` | ~600-780 | EXP distribution, level-ups, move learning, evolution, healing, reward choices |
| `show_game_over` | ~780-795 | Final stats screen |
| `display_team` | ~795-805 | Team display helper |
| `_get_type_name` | ~805-818 | Type ID → name via **ANOTHER `type_map` dict** |
| `main()` | ~818-830 | Entry point |

**Issues:**
1. **`_get_type_name()` has ANOTHER `type_map` dict** — this is approximately the 5th copy of the type ID→name mapping across the codebase
2. **`import random` inside `offer_rewards()`** (line ~693) — should be at module level
3. **CPU never switches** — `battle()` always creates a FIGHT action for CPU (~line 300); `CPUTrainer._try_switch()` is never called
4. **Faint handling done OUTSIDE `TurnManager`** — despite `TurnManager` having `_phase_handle_faints()`, root `main.py` handles faints in its own battle loop
5. **`execute_turn()` handles player switches as special case** — bypasses `TurnManager`'s switch logic entirely
6. **`battle_state['weather']['type']` initialized as string `'None'`** — code elsewhere checks for Python `None` or specific weather strings
7. **Evolution multi-path is random** — when a Pokémon has multiple evolutions (e.g., Eevee), one is chosen randomly with no player input
8. **Comment says "Option 3: Quit" but it's Option 4** — minor comment error (~line 760)
9. **`already_knows` check** uses `m.get('id')` on Move objects — works due to `__getitem__` but confusing mix of object/dict access

---

## 3. Cross-File Dependency Map

### Import Graph (simplified)
```
root main.py
  ├── models/Pokemon.py
  ├── models/team_generation.py → src/repositories.py → src/database.py
  ├── models/cpu.py → src/repositories.py
  ├── models/turn_logic.py → models/ability.py
  ├── models/experience.py
  ├── models/Move.py → src/repositories.py
  └── models/Move_efffect.py

src/run.py
  ├── src/database.py
  ├── src/add_pokemon_data.py → (external export .py files)
  └── src/main.py → src/database.py, src/repositories.py
```

### sys.path Manipulation
Nearly every file manipulates `sys.path` to resolve cross-directory imports. Files doing this:
- `models/Pokemon.py` (triple-nested try/except)
- `models/Move.py`
- `models/cpu.py`
- `models/team_generation.py`
- `models/turn_logic.py`
- `models/ability.py`
- `src/add_pokemon_data.py`
- `src/database.py` (inside methods)
- `src/run.py`
- Root `main.py`

This is fragile and indicates the project would benefit from a proper package structure with a top-level `setup.py`/`pyproject.toml`.

---

## 4. Duplicate / Redundant Code

### 4.1 TYPE_NAMES / type_map Dictionary (5 copies)

| File | Location | Format |
|---|---|---|
| `models/Pokemon.py` | Lines 8-17 | `TYPE_NAMES = {1: 'Normal', ...}` |
| `models/Move.py` | Lines 8-17 | `TYPE_NAMES = {1: 'Normal', ...}` (exact copy) |
| `models/team_generation.py` | Within archetype logic | Type name references |
| Root `main.py` | Lines ~805-818 | `type_map = {1: 'Normal', ...}` inside `_get_type_name()` |
| `models/ability.py` | Within `_calc_type_effectiveness` | Hardcoded type strings |

**Recommendation:** Extract to a single `models/constants.py` or `models/types.py`.

### 4.2 Type Effectiveness Charts (4 copies)

| File | Location | Completeness |
|---|---|---|
| `models/turn_logic.py` | Lines ~1270-1350 | Full 18×18 (authoritative) |
| `models/ability.py` | `_calc_type_effectiveness()` ~1580-1607 | Full 18×18 (independent copy) |
| `models/cpu.py` | `_get_type_effectiveness()` ~400-480 | Partial (8 types only) |
| `models/cpu.py` | `_evaluate_type_advantage()` ~350-400 | Additional partial checks |

**Recommendation:** Single source of truth in a shared module.

### 4.3 Learnset/Evolution Insert Methods (2 copies)

Both `src/database.py` and `src/add_pokemon_data.py` contain:
- `_insert_pokemon_learnsets()` — imports from `pokemon_learnsets_export.py`
- `_insert_pokemon_evolutions()` — imports from `pokemon_evolutions_export.py`

Both import from the same export files and insert into the same tables.

### 4.4 Standalone Database Functions (2 copies)

| Function | `src/database.py` | `src/repositories.py` |
|---|---|---|
| Get all moves | `get_all_moves()` | `MoveRepository.get_all()` |
| Get move by ID | `get_move_details()` | `MoveRepository.get_by_id()` |
| Search by type | `search_moves_by_type()` | `MoveRepository.get_by_type()` |
| Get learnset | `get_pokemon_learnset()` | `PokemonRepository.get_learnset()` |
| Get moves at level | `get_moves_at_level()` | `PokemonRepository.get_moves_at_level()` |

### 4.5 End-of-Turn Status Processing (2 copies)

- `Pokemon.process_end_of_turn_effects()` — handles burn, poison, toxic, leech seed, nightmare, trap, ingrain
- `TurnManager._phase_end_turn()` chain — handles the same effects through a different code path

### 4.6 Move Availability Check (2 copies)

- `Pokemon.can_move()` — sleep, freeze, paralysis, confusion, flinch, attraction
- `TurnManager._can_use_move()` — same checks with slight variations

### 4.7 TeamGenerator Duplicate Methods (4 methods × 2 copies)

In `models/team_generation.py` lines ~1050-1448, standalone functions duplicate class methods:
- `generate_starter_choices()` (standalone) vs `TeamGenerator.generate_starter_choices()` (class)
- `generate_reward_options()` (standalone) vs `TeamGenerator.generate_reward_options()` (class)
- `get_team_summary()` (standalone) vs `TeamGenerator.get_team_summary()` (class)
- `_pokemon_to_data()` (standalone) vs `TeamGenerator._pokemon_to_data()` (class)

The standalone versions have DIFFERENT implementations and reference `species_id` keys not present in repository data.

### 4.8 Protean/Libero Type Change (2 copies in same file)

In `models/ability.py`:
- `check_type_change()` lines ~1415-1430 — handles Protean/Libero
- `on_before_move()` lines ~1540-1570 — handles Protean/Libero again with different implementation

---

## 5. Dead Code & Stubs

### 5.1 Empty/Stub Methods
| Location | Method | Status |
|---|---|---|
| `turn_logic.py` ~2395 | `_process_end_of_turn_items()` | Empty — `pass` |
| `repositories.py` ~240 | `get_evolution_chain()` | Returns `[]` with TODO comment |
| `ability.py` ~820 | `on_after_attacking()` for Analytic | Body is `pass` |

### 5.2 `__main__` Blocks (Test/Demo Code in Production Files)
| File | Approximate Line |
|---|---|
| `models/Move_efffect.py` | End of file |
| `models/cpu.py` | End of file |
| `models/experience.py` | End of file |
| `models/team_generation.py` | `example_usage()` + standalone functions (~800-1448) |
| `src/repositories.py` | End of file |
| `src/add_pokemon_data.py` | End of file |

### 5.3 Unused Imports
| File | Import | Issue |
|---|---|---|
| `models/experience.py` line 6 | `import math` | Never used |

### 5.4 Dead Standalone Functions
The standalone functions at the bottom of `team_generation.py` (lines ~1050-1448) are dead code — the game uses class methods instead. They contain references to `species_id` which doesn't exist in the data.

---

## 6. Inconsistencies & Bugs

### 6.1 Status Value Mismatch
- **`Pokemon` class** uses `self.status = None` for no status condition
- **`turn_logic.py` `_process_start_of_turn_items()`** checks `pokemon.status == 'healthy'`
- **`ability.py`** in various places checks status against string values
- **Impact:** Items dependent on status checks will never trigger correctly

### 6.2 Weather Type Initialization
- **Root `main.py`** initializes `battle_state['weather']['type'] = 'None'` (string)
- **`turn_logic.py`** checks `weather_type = self.battle_state['weather']['type']` and compares to `None` (Python object) or specific weather strings like `'rain'`, `'sun'`
- **Impact:** Weather may never register as "no weather" properly

### 6.3 `_current_user_side` Never Set
- **`turn_logic.py`** references `self._current_user_side` in `_set_user_side_effect()` but this attribute is never initialized or assigned
- **Impact:** Will raise `AttributeError` when side-specific effects (Reflect, Light Screen, etc.) are applied

### 6.4 Move Object Access Pattern Confusion
- `Move` objects support both `move.name` (attribute) AND `move['name']` (dict-style via `__getitem__`)
- Root `main.py` `offer_rewards()` calls `m.get('id')` on Move objects in the `already_knows` check
- Some code paths treat moves as dicts, others as objects — inconsistent throughout

### 6.5 exp_curve 'medium' Not Handled
- Database stores `exp_curve = 'medium'` for some Pokémon
- `ExperienceCurve.exp_for_level()` handles: 'medium_fast', 'medium_slow', 'fast', 'slow', 'erratic', 'fluctuating'
- 'medium' falls through to the default (`medium_fast`) — may be intentional but is undocumented

### 6.6 Sucker Punch in PUNCH_MOVES
- `ability.py` lists `'Sucker Punch'` in `PUNCH_MOVES`
- In the Pokémon games, Sucker Punch is NOT a punching move and should NOT receive Iron Fist boost
- **Impact:** Incorrect damage calculation for Iron Fist users using Sucker Punch

### 6.7 Duplicate Dict Key
- `ability.py` `WEATHER_PASSIVE_ABILITIES` has `'Ice Body'` as a key twice
- Python silently keeps only the last occurrence — earlier data is lost

### 6.8 CPU Never Switches
- `CPUTrainer._try_switch()` exists and implements switch evaluation logic
- Root `main.py` `battle()` (~line 300) always creates `BattleAction(ActionType.FIGHT, ...)` for CPU
- **Impact:** CPU AI cannot switch Pokémon, making battles easier than intended

### 6.9 Faint Handling Bypass  
- `TurnManager._phase_handle_faints()` exists
- Root `main.py` `battle()` handles faints in its own loop (~lines 330-370)
- **Impact:** Dual faint-handling code paths that may diverge in behavior

### 6.10 Reflect Dual Storage
- `_apply_field_effect()` stores Reflect in `battle_state['field_effects']`
- Also stored as a side-specific effect via `_set_user_side_effect()`
- **Impact:** Potential desync between the two storage locations

---

## 7. Broken References & Missing Files

### 7.1 External Data Export Files
The following files are imported by `add_pokemon_data.py` and `database.py` but their presence cannot be guaranteed:

| Expected File | Imported By | Fallback |
|---|---|---|
| `gen5_6_pokemon_export.py` | `add_pokemon_data.py` | Warning printed, data skipped |
| `pokemon_learnsets_export.py` | `add_pokemon_data.py`, `database.py` | Warning printed, table empty |
| `pokemon_evolutions_export.py` | `add_pokemon_data.py`, `database.py` | Warning printed, table empty |
| `abilities_data_export.py` | `add_pokemon_data.py` | Warning printed, table empty |
| `pokemon_abilities_export.py` | `add_pokemon_data.py` | Warning printed, table empty |

Root directory listing confirms `abilities_data_export.py` and `pokemon_abilities_export.py` exist. The others (`gen5_6_pokemon_export.py`, `pokemon_learnsets_export.py`, `pokemon_evolutions_export.py`) were NOT visible in the root listing — they may be in a subdirectory or missing.

### 7.2 Misspelled Filename
- File: `models/Move_efffect.py` (triple 'f')
- All imports must use `from .Move_efffect import ...` or `from models.Move_efffect import ...`
- A rename would require updating ALL import statements

### 7.3 `get_evolution_chain()` TODO
- `src/repositories.py` `PokemonRepository.get_evolution_chain()` returns `[]`
- Any code calling this gets empty results

---

## 8. Temp / Utility Scripts

The following root-level files appear to be temporary/utility scripts not part of the core game:

| File | Purpose | Evidence |
|---|---|---|
| `populate_abilities.py` | One-time ability data population | Utility script name |
| `test_ability_load.py` | Ability loading test | Test prefix in root |
| `test_ability_integration.py` | Ability integration test | Test prefix in root |
| `generate_ability_data.py` | Generates ability data files | Generator script |
| `generate_learnset_report.py` | Generates learnset reports | Generator script |
| `abilities_data_export.py` | Exported ability data | Data export |
| `pokemon_abilities_export.py` | Exported Pokémon-ability mappings | Data export |
| `abilities_raw.json` | Raw ability JSON data | Raw data file |

Additionally, the `proves/` directory contains 18+ test/proof scripts that are separate from the `tests/` directory.

---

## 9. Master Issue Catalog

### Critical (Functional Bugs)

| # | Issue | File(s) | Lines |
|---|---|---|---|
| 1 | `_current_user_side` never set → `AttributeError` | `turn_logic.py` | ~2050-2070 |
| 2 | Weather init `'None'` (string) vs `None` check | Root `main.py` ↔ `turn_logic.py` | ~250, ~200 |
| 3 | Status `'healthy'` vs `None` mismatch | `turn_logic.py` | ~400-420 |
| 4 | Sucker Punch in PUNCH_MOVES (wrong damage) | `ability.py` | ~210 |
| 5 | Duplicate `'Ice Body'` dict key (data loss) | `ability.py` | ~170 |
| 6 | `can_evolve()` raw sqlite3 (bypasses repos) | `Pokemon.py` | ~990-1010 |

### High (Design/Architecture)

| # | Issue | File(s) |
|---|---|---|
| 7 | Type chart duplicated 4× | `turn_logic.py`, `ability.py`, `cpu.py` (×2) |
| 8 | TYPE_NAMES dict duplicated 5× | `Pokemon.py`, `Move.py`, root `main.py`, + others |
| 9 | Learnset/evolution insert duplicated | `database.py` ↔ `add_pokemon_data.py` |
| 10 | 4 methods duplicated in `team_generation.py` | `team_generation.py` lines ~1050-1448 |
| 11 | Standalone DB functions duplicate repositories | `database.py` ↔ `repositories.py` |
| 12 | End-of-turn processing duplicated | `Pokemon.py` ↔ `turn_logic.py` |
| 13 | `can_move()` duplicated | `Pokemon.py` ↔ `turn_logic.py` |
| 14 | Protean/Libero duplicated in same file | `ability.py` (2 methods) |
| 15 | CPU never switches (dead code) | Root `main.py` ↔ `cpu.py` |
| 16 | Faint handling bypasses TurnManager | Root `main.py` |
| 17 | sys.path manipulation in 10+ files | All directories |
| 18 | No connection pooling (open/close per query) | `repositories.py`, all standalone functions |

### Medium (Code Quality)

| # | Issue | File(s) |
|---|---|---|
| 19 | Filename typo `Move_efffect.py` | `models/` |
| 20 | `import math` unused | `experience.py` line 6 |
| 21 | `import random` inside method bodies | `Pokemon.py`, root `main.py` |
| 22 | `__main__` blocks in 6+ production files | Various |
| 23 | `_apply_field_effect()` 280 lines | `turn_logic.py` |
| 24 | `_apply_other_effect()` 230 lines | `turn_logic.py` |
| 25 | `SpecialEffect.apply()` 200-line if/elif | `Move_efffect.py` |
| 26 | f-string SQL ORDER BY (injection vector) | `repositories.py` |
| 27 | `get_evolution_chain()` is TODO stub | `repositories.py` |
| 28 | `_process_end_of_turn_items()` empty stub | `turn_logic.py` |
| 29 | `Analytic` ability is `pass` stub | `ability.py` |
| 30 | `exp_curve 'medium'` undocumented fallthrough | `experience.py` |

### Low (Minor/Cosmetic)

| # | Issue | File(s) |
|---|---|---|
| 31 | Comment "Option 3: Quit" but it's option 4 | Root `main.py` ~760 |
| 32 | Dual entry points (confusing project structure) | Root `main.py` vs `src/run.py` |
| 33 | `models/__init__.py` incomplete exports | `models/__init__.py` |
| 34 | Standalone functions create new instances per call | `database.py`, `add_pokemon_data.py` |
| 35 | Evolution multi-path random (no player choice) | Root `main.py` ~690 |
| 36 | Silent ImportError on missing export files | `add_pokemon_data.py`, `database.py` |
| 37 | Reflect dual storage (field_effects + side) | `turn_logic.py` |
| 38 | Dead standalone functions in team_generation.py | `team_generation.py` ~1050-1448 |

---

**Total Issues Found: 38**  
- Critical: 6  
- High: 12  
- Medium: 12  
- Low: 8  

---

*End of audit report. No files were modified during this analysis.*
