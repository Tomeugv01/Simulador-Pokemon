# Pokemon Database structure

## Db structure

Pokemon {
- id
- name 
- type1
- type2
- hp
- attack
- deffense
- special_attack
- special_deffense
- speed
- total_stats

}

Move {
- id
- name 
- type1
- power
- accuracity
- pp
- type (physical, special)
- archetype (phiscal_sweeper, special_sweeper, tank, etc)
- effect (JSON)

}

Ability {
- id
- name 
- effect (JSON)

}

# Team Generation

## Pokemon selector

- Using different ranges of the total_stats value, random teams will be seleected for the opponent, creating an enviroment where teams are created with a difficulty progression is as best reflected as possible
- A similar method will be implemented for the player team, a first team of pokemon will be given with a predetermined range of stats and after each encounter, he will be givven the option to add or swap a new mon of progresivly stronger characteristics

## Move selector

- Once a Pokemon is selected to be added to a team, the move selection proces will begin.
- Depending on the relative value of each stat of the mon (what percentage of their stats are alocated to each one) it will be assigned to a different archetype and thus it will get assigned 4 differnt random moves that fall onto this archetypes.
- In the probable case that a pokemon falls into more than one of these archetypes, its 4 moves will be randomly selected between all of the possible pools of moves
- After each encounter, instead of adding a new pokemon to his team, the player will also get the option to replace one of his moves with an other one of ANY archetype of his liking.

# Pokémon Battle Engine Turn Resolution Guide

## Complete Turn Flowchart
[Turn Start] → [Action Selection] → [Begin Turn] → [Priority Brackets] → [Speed Calculation] → [Execute Actions] → [Turn End]


---

## Phase 1: Action Selection

Each player secretly selects an action for each Pokémon:

- **Fight:** Use a move
- **Switch:** Switch with a Pokémon from the bench

**Key Rule:** Switching occurs before most moves, causing targeting moves to fail (except Pursuit).

---

## Phase 2: Begin Turn (Pre-Turn Effects)

### 2.1 Weather Check
- Check for weather condition expiration
- Apply weather damage (Sandstorm, Hail)

### 2.2 Field Effect Check
- Check Terrains, Trick Room, Gravity duration

### 2.3 Ability Check (Start of Turn)
- Weather abilities: Forecast, Sand Stream, Snow Warning
- Status abilities: Poison Heal, Hydration
- Other: Shed Skin, Speed Boost

### 2.4 Status Ailment Damage & Check
- **Poison/Bad Poison:** Apply damage (increasing for Bad Poison)
- **Burn:** Apply damage and reduce Attack
- **Sleep:** Check for wake-up (decrement sleep counter)
- **Freeze:** Check for thaw (~20% chance)
- **Confusion:** Check for self-hit

### 2.5 Item Check (Start of Turn)
- Leftovers (heal)
- Black Sludge (heal Poison/damage others)
- Flame Orb (activate burn)

### 2.6 Roost Effect End
- Restore Flying-type if Roost was used last turn

### 2.7 Forced Switching
- Check for trapping (Arena Trap, Mean Look)
- Execute player-requested switches

---

## Phase 3: Action Resolution Order

### Priority Brackets (Highest to Lowest)

| Priority | Action Type | Examples |
|----------|-------------|----------|
| Bracket 7 | Run/Switch | Switching, Poké Balls |
| Bracket 6 | Mega Evolution | Mega Evolution |
| Bracket 5 | Pursuit | Pursuit (on switch) |
| Bracket 4+ | Priority Moves | Protect, Extreme Speed, Aqua Jet |
| Bracket 0 | Standard Moves | Tackle, Flamethrower, Hyper Beam |
| Bracket -1 to -7 | Negative Priority | Vital Throw, Trick Room, Roar |

### Action Execution Sub-routine

#### A. Determine Action Order
- Calculate current Speed for all acting Pokémon
- Apply modifiers: Paralysis, Choice Scarf, abilities, field effects
- Highest Speed acts first within bracket

#### B. Execute Action

**For MOVES:**
1. **Pre-Move Checks**
   - Full Paralysis/Infatuation (25% fail chance)
   - Disable/Imprison status
   - Gravity restrictions
   - Heal Block/Taunt restrictions
   - Charge turns (Fly, Dig)

2. **Determine Targets**
   - Single, all foes, etc.

3. **Protection Check**
   - Protect, Detect, King's Shield
   - Success chance decreases with consecutive use

4. **Accuracy Check**
   - Formula: `(Move Accuracy) × (User Accuracy / Target Evasion) × (Modifiers)`
   - Some moves bypass accuracy (Swift, Aura Sphere)

5. **Critical Hit Check**
   - Ignores user's negative stat stages and target's positive stages

6. **Damage Calculation**
  - Damage = `((((2 × Level / 5 + 2) × Power × Attack / Defense) / 50) + 2) × Modifiers`

   - Modifiers: STAB, Type Effectiveness, Weather, Items, Abilities

7. **Secondary Effects**
- Status infliction
- Stat changes
- Recoil/Healing

8. **Self-KO Check**
- Recoil, Life Orb damage

**For SWITCHES:**
- Pokémon recalled
- New Pokémon sent out
- Entry hazards applied
- Switch-in abilities activate

#### C. Faint Check
- Check for fainted Pokémon after each action
- Fainted Pokémon cannot act
- Replacement chosen but not sent until turn end

---

## Phase 4: Turn End (End-of-Turn Effects)

### 4.1 Weather & Field Effect Damage
- Hail, Sandstorm damage

### 4.2 Ability Check (End of Turn)
- Bad Dreams (damage sleeping foes)
- Ice Body/Rain Dish (healing)

### 4.3 Item Check (End of Turn)
- Shell Bell (heal if damage dealt)

### 4.4 Status Ailment Damage
- Poison/Burn damage application

### 4.5 Volatile Status End
- Check Leech Seed, Curse, binding moves
- Apply their effects

### 4.6 Turn Counters Decrement
- Weather conditions
- Trick Room, Terrain, Tailwind
- Reflect/Light Screen
- Disable/Taunt/Encore

### 4.7 Send Out Fainted Pokémon
- New Pokémon sent to replace fainted ones
- Entry hazards applied
- Switch-in abilities activate

### 4.8 Win/Loss Condition Check
- Check if any trainer has no usable Pokémon
- End battle if condition met

---

