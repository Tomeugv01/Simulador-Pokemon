# Pokemon Battle Simulator - Roguelike Edition

A roguelike console-based Pokemon battle game featuring intelligent CPU opponents, dynamic difficulty scaling, and strategic team building.

---

## 🎮 Quick Start

```bash
# Play the full game
python main.py

# Watch an automated demo
python demo_game.py
```

**📖 See [GAME_GUIDE.md](GAME_GUIDE.md) for complete gameplay instructions!**

---

## 🌟 What is This?

This is a **roguelike Pokemon battle simulator** where you:
1. **Choose a team** of 3 starter Pokemon
2. **Battle** increasingly difficult CPU opponents
3. **Earn rewards** and strengthen your team
4. **Achieve** the longest winning streak possible

**⚠️ One loss ends your run!**

---

## ✨ Core Features

### 🎮 Complete Game Loop
- **Starter Selection**: Choose 3 Pokemon from 9 options across 3 groups
- **Progressive Battles**: Face opponents that scale with your progress
- **Reward System**: Add new Pokemon or continue with current team
- **Win Streaks**: Track your best run and try to beat it

### 🤖 Intelligent CPU AI
- Based on **Generation 4 Trainer AI** rules
- Multiple difficulty levels: Easy → Normal → Hard → Expert
- Strategic move selection using scoring flags:
  - Type effectiveness calculations (+10/-10 score modifiers)
  - HP-based decision making (healing priority at low HP)
  - Setup move timing (stat boosts when advantageous)
  - Immunity checking (avoid immune types)
  - STAB consideration (Same Type Attack Bonus)

### ⚖️ Balanced Progression
- **TSB (Total Stat Budget)** scaling ensures fair matchups
- **Power Cap System**: Prevents low-level Pokemon from learning overpowered moves
  - Level 5 Caterpie: Max 40 power moves
  - Level 50 Mewtwo: Max 115 power moves
- **Team Compositions**: Balanced, Glass Cannon, Ace Team, Swarm
- **Archetype System**: 7 distinct Pokemon roles
  - Physical Attacker, Special Attacker, Tank
  - Glass Cannon, Speedster, Mixed Attacker, Wall

### ⚔️ Battle System
- **Turn-based combat** with speed-based turn order
- **Type effectiveness** with full type chart (18 types)
- **Move categories**: Physical, Special, and Status moves
- **Damage calculation** based on Pokemon stats and move power
- **Strategic switching** between team members

---

## 📊 Difficulty Scaling

| Round | Opponent Level | Opponent TSB | Team Size | CPU Difficulty |
|-------|---------------|--------------|-----------|----------------|
| 1-2   | 5-9          | 250-280      | 3         | Easy          |
| 3-5   | 11-15        | 300-360      | 3-4       | Normal        |
| 6-10  | 21-35        | 400-500      | 4-5       | Hard          |
| 10+   | 40+          | 500-600+     | 5-6       | Expert        |

As you progress:
- Opponents get **higher stats** (TSB increases)
- Opponents reach **higher levels**
- Teams get **larger** (3 → 6 Pokemon)
- AI gets **smarter** (more scoring flags active)

---

## 🎯 How to Play

### Battle Flow
Each battle happens in **turns**, where you and your opponent choose moves:

1. **Choose Your Action**
   - **Fight**: Select one of your 4 moves
   - **Switch**: Change to a different Pokemon
   - **Forfeit**: End your run

2. **CPU Chooses Its Move**
   - Uses AI scoring to evaluate all options
   - Considers type matchups, HP, and strategy

3. **Moves Execute in Order**
   - **Speed determines order**: Faster Pokemon goes first
   - Moves deal damage or apply effects
   - Check for fainted Pokemon

4. **Battle Continues**
   - Until one side has no Pokemon left
   - Winner proceeds (or game over if you lose)

### Strategy Tips
- **Type Coverage**: Build a team with diverse types
- **Save Your Ace**: Don't sacrifice your strongest Pokemon early
- **Watch HP Thresholds**: Heal before critical damage
- **Predict CPU**: AI patterns become recognizable
- **Know When to Quit**: Save your streak by ending after a win

---

## 🗂️ Project Structure

```
Simulador-Pokemon/
├── main.py                     # Main game loop (PLAY HERE!)
├── demo_game.py               # Automated demo
├── GAME_GUIDE.md              # Complete gameplay guide
├── README.md                  # This file
│
├── data/
│   └── pokemon_battle.db      # 151 Pokemon, 428 moves, 111 effects
│
├── models/
│   ├── Pokemon.py             # Pokemon class
│   ├── Move.py                # Move class
│   ├── team_generation.py    # Team building & scaling (1100+ lines)
│   ├── cpu.py                 # CPU AI (570 lines)
│   └── turn_logic.py          # Battle system (420 lines)
│
├── src/
│   ├── repositories.py        # Database access
│   └── database.py            # DB initialization
│
└── Docs/
    ├── Features.md            # Feature specifications
    ├── Turn_logic.md          # Turn system details
    ├── Cpu_functionality.md   # AI behavior documentation
    └── Run_generation.md      # Team generation docs
```

---

## 🔧 Technical Details

### Database
- **SQLite** database with normalized schema
- **151 Generation 1 Pokemon** with complete stats
- **428 moves** across all categories
- **111 unique move effects**
- No duplicates, fully verified data

### Team Generation
- **TSB-based scaling**: Teams balanced by total stats
- **Level calculation**: Scales with round progression
- **Archetype detection**: Automatic role assignment
- **Move selection**: 4 moves per Pokemon based on archetype
- **Power caps**: Level-appropriate moves only

### CPU AI System
- **Generation 4 Trainer AI** implementation
- **5 Behavior Flags**:
  1. BASIC - Avoid immunities, redundant moves
  2. EVALUATE_ATTACK - Type effectiveness scoring
  3. EXPERT - Setup timing, STAB bonuses
  4. CHECK_HP - HP-based priorities
  5. PRIORITIZE_DAMAGE - Prefer high power moves
- **Scoring system**: Moves start at 100, flags add/subtract
- **Difficulty scaling**: More flags = smarter AI

### Battle System
- **5-phase turn resolution**:
  1. Switch Phase
  2. Priority Move Phase
  3. Normal Move Phase
  4. End of Turn Phase
  5. Faint Phase
- **Damage formula**: Based on Gen 1-4 mechanics (simplified)
- **Type chart**: Full 18-type effectiveness matrix

---

## 🧪 Testing & Demo

Run the automated demo to see all systems in action:

```bash
python demo_game.py
```

**Demo showcases:**
- Starter selection (3 groups of 3 Pokemon)
- Opponent generation with scaling
- CPU AI decision-making at all difficulty levels
- Round progression (levels 1, 3, 5, 10)
- Reward system
- All team compositions (Balanced, Glass Cannon, Ace, Swarm)

---

## 📈 Game Systems

### Archetypes
Pokemon are assigned roles based on stat distribution:

| Archetype | Characteristics | Example Moves |
|-----------|----------------|---------------|
| Physical Attacker | High Attack | Earthquake, Body Slam, Close Combat |
| Special Attacker | High Sp. Attack | Flamethrower, Psychic, Surf |
| Tank | High HP/Def | Recover, Rest, Body Press |
| Glass Cannon | High offense, low defense | Explosion, Overheat |
| Speedster | High Speed | Quick Attack, Extreme Speed |
| Mixed Attacker | Balanced offenses | Varied movepool |
| Wall | High defenses | Light Screen, Reflect |

### Power Cap Formula
```python
# Level-based cap
if level <= 10:
    cap = 40 + (level * 2)  # 40-60
elif level <= 20:
    cap = 50 + ((level-10) * 3)  # 50-80
elif level <= 40:
    cap = 60 + ((level-20) * 2)  # 60-100
elif level <= 60:
    cap = 70 + ((level-40) * 2.5)  # 70-120
else:
    cap = 150

# TSB modifiers
if TSB < 300: cap -= 10
elif TSB >= 400: cap += 10
elif TSB >= 500: cap += 20

cap = max(40, cap)  # Minimum 40 power
```

### Team Compositions

**BALANCED**: All Pokemon near average TSB (most common)

**GLASS CANNON**: 1 strong (max TSB), 2 medium, 3 weak

**ACE TEAM**: 1-2 very strong, rest medium

**SWARM**: All Pokemon below average TSB

---

## 🎓 Learning From This Project

This project demonstrates:
- **Database Design**: Normalized schema, foreign keys, indexes
- **OOP Principles**: Clean class hierarchies, encapsulation
- **AI Implementation**: Scoring systems, decision trees
- **Game Balance**: Statistical budgets, scaling formulas
- **Roguelike Design**: Progression curves, risk/reward
- **Code Organization**: Modular systems, clear separation

---

## 🚀 Future Enhancements

Potential additions:
- [ ] Items and held items system
- [ ] Status conditions (paralysis, burn, poison)
- [ ] Weather effects (rain, sun, sandstorm)
- [ ] Abilities system (Levitate, Intimidate, etc.)
- [ ] More AI flags (WEATHER, HARASSMENT, BATON_PASS)
- [ ] Battle animations/visual effects
- [ ] Save/load system
- [ ] Leaderboards and achievements
- [ ] Post-game content and hard mode

---

## 📝 Documentation

- **[GAME_GUIDE.md](GAME_GUIDE.md)**: Complete player's guide
- **[Features.md](Docs/Features.md)**: Feature specifications
- **[Turn_logic.md](Docs/Turn_logic.md)**: Turn system details
- **[Cpu_functionality.md](Docs/Cpu_functionality.md)**: AI documentation
- **[Run_generation.md](Docs/Run_generation.md)**: Team generation

---

## 🎮 Credits

Built with:
- **Python 3.x** - Core language
- **SQLite** - Database engine
- **Generation 1 Pokemon** - 151 classic Pokemon
- **Generation 4 AI Rules** - Trainer battle AI
- **Modern Game Design** - Roguelike mechanics

---

**Good luck, Trainer! How many rounds can you conquer? 🏆**

