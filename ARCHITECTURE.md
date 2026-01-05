# Pokemon Battle Simulator - System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         POKEMON BATTLE SIMULATOR                     │
│                         Roguelike Edition v1.0                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                            MAIN GAME LOOP                            │
│                              (main.py)                               │
├─────────────────────────────────────────────────────────────────────┤
│ • Welcome Screen                                                     │
│ • Starter Selection (3 groups × 3 options)                          │
│ • Battle Loop                                                        │
│   - Generate Opponent                                               │
│   - Execute Battle                                                   │
│   - Handle Victory/Defeat                                            │
│ • Reward System                                                      │
│ • Win Streak Tracking                                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
        │ Team          │ │ CPU           │ │ Battle        │
        │ Generation    │ │ AI            │ │ System        │
        └───────────────┘ └───────────────┘ └───────────────┘


═══════════════════════════════════════════════════════════════════════
LAYER 1: GAME LOGIC SYSTEMS
═══════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────┐
│              TEAM GENERATION SYSTEM (team_generation.py)             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ TSB (Total Stat Budget) Scaling                             │   │
│  │ • Calculate round-based TSB range                           │   │
│  │ • Round 1: 250-280 TSB                                      │   │
│  │ • Round 10: 500+ TSB                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Team Composition Patterns                                    │   │
│  │ • BALANCED: All Pokemon similar strength                    │   │
│  │ • GLASS_CANNON: 1 strong, 2 mid, 3 weak                    │   │
│  │ • ACE_TEAM: 1-2 very strong, rest medium                   │   │
│  │ • SWARM: All below average                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Archetype System (7 types)                                  │   │
│  │ • Physical Attacker - High Attack                           │   │
│  │ • Special Attacker - High Sp. Attack                        │   │
│  │ • Tank - High HP/Defense                                    │   │
│  │ • Glass Cannon - High offense, low defense                  │   │
│  │ • Speedster - High Speed                                    │   │
│  │ • Mixed Attacker - Balanced offenses                        │   │
│  │ • Wall - High defenses                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Power Cap System                                            │   │
│  │ • Level-based move power limits                             │   │
│  │   - Level 1-10:  40-60 power                               │   │
│  │   - Level 11-20: 50-80 power                               │   │
│  │   - Level 21-40: 60-100 power                              │   │
│  │   - Level 41-60: 70-120 power                              │   │
│  │   - Level 61+:   150 power max                             │   │
│  │ • TSB modifiers: -10 (weak) to +20 (strong)               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Key Methods                                                  │   │
│  │ • generate_starter_choices()                                │   │
│  │ • generate_opponent_team(round_number, size, composition)  │   │
│  │ • generate_reward_options(player_team)                     │   │
│  │ • _select_moves_for_pokemon(pokemon, archetype, level)     │   │
│  │ • _calculate_max_move_power(pokemon, level)                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                    CPU AI SYSTEM (cpu.py)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Behavior Flags (Generation 4 Rules)                         │   │
│  │                                                              │   │
│  │  BASIC FLAG (Easy+)                                         │   │
│  │  • Check immunities (-10 if immune)                         │   │
│  │  • Avoid redundant status moves (-10)                       │   │
│  │  • Avoid wasted turns (already has status)                  │   │
│  │                                                              │   │
│  │  EVALUATE_ATTACK FLAG (Normal+)                             │   │
│  │  • Super effective (+10)                                    │   │
│  │  • Not very effective (-10)                                 │   │
│  │  • Consider type matchups                                   │   │
│  │                                                              │   │
│  │  EXPERT FLAG (Hard+)                                        │   │
│  │  • Setup timing (+5 when HP high & faster)                  │   │
│  │  • Aggressive when low HP (-5 non-damage)                   │   │
│  │  • STAB preference (+3 same-type)                           │   │
│  │                                                              │   │
│  │  CHECK_HP FLAG (Hard+)                                      │   │
│  │  • Critical HP healing (<30% = +20)                         │   │
│  │  • Low HP healing (<50% = +10)                              │   │
│  │  • Finish off weak targets (<25% = +10)                     │   │
│  │  • Avoid overkill (100+ power vs <15% = -5)                │   │
│  │                                                              │   │
│  │  PRIORITIZE_DAMAGE FLAG (Expert)                            │   │
│  │  • High power moves (+10 if ≥100 power)                     │   │
│  │  • Good power moves (+5 if ≥80 power)                       │   │
│  │  • Penalize status moves (-5)                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Difficulty Levels                                           │   │
│  │ • EASY:   BASIC only                                        │   │
│  │ • NORMAL: BASIC + EVALUATE_ATTACK                           │   │
│  │ • HARD:   BASIC + EVALUATE_ATTACK + CHECK_HP                │   │
│  │ • EXPERT: All 5 flags active                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Decision Process                                            │   │
│  │ 1. Get all available moves with PP > 0                      │   │
│  │ 2. Initialize all move scores to 100                        │   │
│  │ 3. Apply flag modifiers sequentially                        │   │
│  │ 4. Find moves with highest score                            │   │
│  │ 5. Random selection if multiple tied                        │   │
│  │ 6. Return chosen move with reasoning                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                  BATTLE SYSTEM (turn_logic.py)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 5-Phase Turn Resolution                                     │   │
│  │                                                              │   │
│  │  Phase 1: SWITCH PHASE                                      │   │
│  │  • Process all switch actions                               │   │
│  │  • Update active Pokemon                                    │   │
│  │                                                              │   │
│  │  Phase 2: PRIORITY MOVE PHASE                               │   │
│  │  • Execute high priority moves first                        │   │
│  │  • Speed-based order within priority                        │   │
│  │                                                              │   │
│  │  Phase 3: NORMAL MOVE PHASE                                 │   │
│  │  • Speed-based turn order                                   │   │
│  │  • Execute damaging and status moves                        │   │
│  │  • Apply type effectiveness                                 │   │
│  │  • Calculate damage                                         │   │
│  │                                                              │   │
│  │  Phase 4: END OF TURN PHASE                                 │   │
│  │  • Trigger end-of-turn effects                              │   │
│  │  • Status damage (poison, burn)                             │   │
│  │  • Weather damage                                           │   │
│  │                                                              │   │
│  │  Phase 5: FAINT PHASE                                       │   │
│  │  • Check for 0 HP Pokemon                                   │   │
│  │  • Force switches                                           │   │
│  │  • Check for battle end                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Damage Formula (Simplified Gen 1-4)                         │   │
│  │                                                              │   │
│  │  Base = ((2*Level/5 + 2) * Power * Attack / Defense / 50 + 2)│   │
│  │  Random Factor = 0.85x - 1.0x                               │   │
│  │  STAB = 1.5x if move type matches Pokemon type              │   │
│  │  Type Effectiveness = 2x, 1x, 0.5x, or 0x                   │   │
│  │  Final Damage = Base * Random * STAB * Effectiveness        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
LAYER 2: DATA MODELS
═══════════════════════════════════════════════════════════════════════

┌──────────────────┐         ┌──────────────────┐
│  Pokemon Class   │         │   Move Class     │
├──────────────────┤         ├──────────────────┤
│ • id             │         │ • id             │
│ • name           │         │ • name           │
│ • level          │         │ • type           │
│ • current_hp     │         │ • category       │
│ • max_hp         │         │ • power          │
│ • attack         │         │ • accuracy       │
│ • defense        │         │ • pp_current     │
│ • sp_attack      │         │ • pp_max         │
│ • sp_defense     │         │ • priority       │
│ • speed          │         │ • causes_damage  │
│ • moves[]        │ ───────>│ • effect         │
└──────────────────┘         └──────────────────┘


═══════════════════════════════════════════════════════════════════════
LAYER 3: DATA ACCESS
═══════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────┐
│                    REPOSITORY LAYER (repositories.py)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────┐          ┌──────────────────────┐        │
│  │ PokemonRepository    │          │ MoveRepository       │        │
│  ├──────────────────────┤          ├──────────────────────┤        │
│  │ • get_all()          │          │ • get_all()          │        │
│  │ • get_by_id(id)      │          │ • get_by_id(id)      │        │
│  │ • get_by_name(name)  │          │ • get_by_name(name)  │        │
│  │ • get_in_tsb_range() │          │ • get_by_type(type)  │        │
│  └──────────────────────┘          └──────────────────────┘        │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DATABASE (pokemon_battle.db)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   pokemon    │  │    moves     │  │  move_effects│             │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤             │
│  │ 151 Pokemon  │  │ 428 Moves    │  │ 111 Effects  │             │
│  │ • Gen 1 only │  │ • No dupes   │  │ • Unique     │             │
│  │ • Full stats │  │ • All types  │  │ • Verified   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                       │
│  ┌──────────────┐                                                   │
│  │    types     │   18 Types: Normal, Fire, Water, Electric,       │
│  ├──────────────┤   Grass, Ice, Fighting, Poison, Ground, Flying,  │
│  │ 18 Types     │   Psychic, Bug, Rock, Ghost, Dragon, Dark,       │
│  │ Full chart   │   Steel, Fairy                                    │
│  └──────────────┘                                                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
DATA FLOW: TYPICAL BATTLE
═══════════════════════════════════════════════════════════════════════

1. GAME START
   main.py → show_welcome_screen()

2. STARTER SELECTION
   main.py → team_generation.generate_starter_choices()
   → Returns 3 groups of 3 Pokemon
   → Player chooses 1 from each group
   → player_team = [Pokemon, Pokemon, Pokemon]

3. ROUND START
   main.py → team_generation.generate_opponent_team(round, size, comp)
   → Calculates TSB range for round
   → Selects composition pattern
   → Generates Pokemon with archetypes
   → Applies power caps to moves
   → Returns opponent_team

4. BATTLE LOOP
   For each turn:
   
   A. PLAYER INPUT
      main.py → get_player_action(player_pokemon, opponent_pokemon)
      → Display menu (Fight/Switch/Forfeit)
      → Get player choice
      → Return action
   
   B. CPU DECISION
      main.py → cpu.choose_move(cpu_pokemon, player_pokemon)
      → Convert Move objects to dicts
      → Initialize all move scores to 100
      → Apply BASIC flag modifiers
      → Apply EVALUATE_ATTACK flag modifiers
      → Apply EXPERT flag modifiers (if hard+)
      → Apply CHECK_HP flag modifiers (if hard+)
      → Apply PRIORITIZE_DAMAGE flag modifiers (if expert)
      → Select highest scoring move
      → Return {'move': dict, 'score': int, 'reason': str}
   
   C. TURN EXECUTION
      main.py → execute_simple_turn(player_poke, cpu_poke, actions)
      → Determine turn order (speed comparison)
      → Execute moves in order
      → Calculate damage:
        * Get attacker stats (Atk or SpA)
        * Get defender stats (Def or SpD)
        * Apply damage formula
        * Apply STAB (1.5x if same type)
        * Apply type effectiveness
      → Update Pokemon HP
      → Check for faints
   
   D. FAINT HANDLING
      If Pokemon faints:
      → Remove from team
      → Check for team wipe (battle end)
      → Force switch to next Pokemon

5. BATTLE END
   If player wins:
   → main.py → team_generation.generate_reward_options(player_team)
   → Display reward choices
   → Player selects: add Pokemon, continue, or quit
   → Full heal team
   → round++
   → Return to step 3
   
   If player loses:
   → main.py → show_game_over()
   → Display final stats (wins, team)
   → End game

6. PROGRESSION
   Each round:
   • Opponents get +30 TSB on average
   • Opponent levels increase by ~2
   • Team sizes grow (3 → 6)
   • AI difficulty scales (Easy → Expert)
   • Compositions vary (Balanced, Glass Cannon, etc.)


═══════════════════════════════════════════════════════════════════════
SCORING EXAMPLE: CPU CHOOSING A MOVE
═══════════════════════════════════════════════════════════════════════

Scenario: Starmie vs Charizard (both level 50, full HP)
CPU Difficulty: HARD
Available moves: Surf, Ice Beam, Psychic, Thunder Wave

MOVE SCORING PROCESS:

Initial Scores:
• Surf:         100
• Ice Beam:     100
• Psychic:      100
• Thunder Wave: 100

BASIC FLAG:
• Surf:         100 (no change - not immune)
• Ice Beam:     100 (no change - not immune)
• Psychic:      100 (no change - not immune)
• Thunder Wave: 100 (no change - status move, not redundant)

EVALUATE_ATTACK FLAG:
• Surf:         110 (Water vs Fire = super effective +10)
• Ice Beam:     105 (Ice vs Fire/Flying = 1.5x +5)
• Psychic:      100 (Psychic vs Fire/Flying = neutral)
• Thunder Wave: 100 (status move, no type modifier)

EXPERT FLAG:
• Surf:         113 (Water type, Starmie is Water = STAB +3)
• Ice Beam:     105 (Ice type, no STAB)
• Psychic:      103 (Psychic type, Starmie is Water/Psychic = STAB +3)
• Thunder Wave: 100 (status move)

CHECK_HP FLAG:
• All moves: no change (both Pokemon at full HP)

FINAL SCORES:
• Surf:         113 ← HIGHEST (super effective + STAB)
• Ice Beam:     105
• Psychic:      103
• Thunder Wave: 100

CPU CHOOSES: Surf
Reason: "Score: 113, Modifiers: Type advantage +10, STAB +3"


═══════════════════════════════════════════════════════════════════════
KEY ALGORITHMS
═══════════════════════════════════════════════════════════════════════

TSB CALCULATION:
  tsb = hp + attack + defense + sp_attack + sp_defense + speed

ROUND TSB RANGE:
  base_tsb = 250 + (round_number - 1) * 30
  variance = base_tsb * (10 + round_number * 2) / 100
  tsb_min = max(200, base_tsb - variance)
  tsb_max = min(600, base_tsb + variance)

POWER CAP FORMULA:
  if level <= 10:
    cap = 40 + (level * 2)
  elif level <= 20:
    cap = 50 + ((level - 10) * 3)
  elif level <= 40:
    cap = 60 + ((level - 20) * 2)
  elif level <= 60:
    cap = 70 + ((level - 40) * 2.5)
  else:
    cap = 150
  
  # TSB modifiers
  if tsb < 300: cap -= 10
  elif tsb >= 400: cap += 10
  elif tsb >= 500: cap += 20
  
  cap = max(40, cap)

DAMAGE CALCULATION:
  base = ((2 * level / 5 + 2) * power * attack / defense / 50 + 2)
  random_factor = random(0.85, 1.0)
  stab = 1.5 if move_type in pokemon_types else 1.0
  effectiveness = calculate_type_effectiveness(move_type, target_types)
  damage = int(base * random_factor * stab * effectiveness)


═══════════════════════════════════════════════════════════════════════
CONCLUSION
═══════════════════════════════════════════════════════════════════════

This architecture provides:
✓ Clear separation of concerns
✓ Modular, testable components
✓ Scalable difficulty progression
✓ Intelligent AI decision-making
✓ Fair game balance through math
✓ Extensible design for future features

Total System: ~3140 lines of Python code
Database: 151 Pokemon, 428 Moves, 111 Effects
Status: FULLY FUNCTIONAL AND PLAYABLE

To play: python main.py
To demo: python demo_game.py
```
