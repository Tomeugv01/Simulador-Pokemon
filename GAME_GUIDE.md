# Pokemon Battle Simulator - Game Guide

## Welcome to the Pokemon Battle Simulator!

This is a roguelike Pokemon battle game where you build a team, face increasingly difficult opponents, and try to achieve the longest winning streak possible.

## Quick Start

To play the game, run:
```bash
python main.py
```

## Game Overview

### Core Concept
- **Roguelike Progression**: One loss ends your run
- **Dynamic Scaling**: Opponents get stronger each round
- **Team Building**: Choose your team carefully and earn rewards
- **Strategic Battles**: CPU AI uses Generation 4 trainer logic

## How to Play

### 1. Starter Selection

At the start of each run, you'll choose 3 Pokemon from 3 different groups:
- Each group contains 3 Pokemon options
- Choose ONE from each group
- Consider stats, types, and movesets
- Your choices form your starting team

**What to look for:**
- **TSB (Total Stat Budget)**: Higher = stronger Pokemon
- **Type Coverage**: Diverse types handle more situations
- **Role**: Attackers, Tanks, Speedsters each have advantages
- **Moves**: Check if Pokemon have useful attacking/support moves

### 2. Battle System

Each round, you face an opponent team:
- Team size grows with rounds (3 → 4 → 5 → 6)
- CPU difficulty increases (Easy → Normal → Hard)
- Opponents use intelligent AI to choose moves

**Your Actions:**
- **Fight**: Choose one of your Pokemon's 4 moves
- **Switch**: Swap to a different Pokemon
- **Forfeit**: End the run (saves your record)

**Battle Flow:**
1. Choose your action
2. CPU chooses its move
3. Faster Pokemon goes first (based on Speed stat)
4. Moves execute and deal damage
5. Check for fainted Pokemon
6. Repeat until one side has no Pokemon left

### 3. Progression System

**Round Scaling:**
- **Round 1-2**: Easy opponents (TSB 250-280, Level 5-9)
- **Round 3-5**: Normal opponents (TSB 300-360, Level 11-15)
- **Round 6-10**: Hard opponents (TSB 400-500, Level 21-35)
- **Round 10+**: Expert opponents (TSB 500+, Level 40+)

**Difficulty Increases:**
- Higher opponent levels and stats
- More Pokemon per team
- Smarter AI decision-making
- Better team compositions

### 4. Rewards

After each victory, you can:
- **Add New Pokemon**: Get a new team member (if you have room)
- **Continue**: Proceed to next round with current team
- **End Run**: Save your win streak and quit

Your team is fully healed after each battle!

## Game Mechanics

### Stats Explained

Each Pokemon has 6 core stats:
- **HP**: Health Points - higher = more survivability
- **Attack**: Physical move power
- **Defense**: Physical damage resistance
- **Sp. Attack**: Special move power
- **Sp. Defense**: Special damage resistance
- **Speed**: Turn order - higher goes first

**TSB (Total Stat Budget)**: Sum of all base stats
- Weak Pokemon: 200-300 TSB
- Medium Pokemon: 300-450 TSB
- Strong Pokemon: 450-600 TSB
- Legendary Pokemon: 600+ TSB

### Move Categories

**Physical Moves:**
- Use Attack vs Defense
- Examples: Tackle, Scratch, Body Slam

**Special Moves:**
- Use Sp. Attack vs Sp. Defense
- Examples: Flamethrower, Psychic, Surf

**Status Moves:**
- Don't deal damage
- Apply effects: stat changes, status conditions, field effects
- Examples: Swords Dance, Thunder Wave, Light Screen

### Type Effectiveness

Types interact strategically:
- **Super Effective** (2x damage): Fire vs Grass, Water vs Fire, etc.
- **Not Very Effective** (0.5x damage): Fire vs Water, Grass vs Fire, etc.
- **Immune** (0x damage): Normal vs Ghost, Electric vs Ground, etc.

The CPU AI considers type matchups when choosing moves!

### CPU AI Behavior

The AI uses scoring flags to evaluate moves:

**BASIC Flag** (Easy+):
- Avoids type-immune moves
- Won't use redundant status moves
- Checks if setup moves are useful

**EVALUATE_ATTACK Flag** (Normal+):
- Prefers super effective moves (+10 score)
- Avoids not very effective moves (-10 score)

**CHECK_HP Flag** (Hard+):
- Prioritizes healing at low HP (+20 score)
- Attempts to finish off weak opponents (+10 score)
- Avoids overkill on near-fainted Pokemon (-5 score)

**EXPERT Flag** (Expert):
- Uses setup moves when appropriate (+5 score)
- Considers STAB (Same Type Attack Bonus) (+3 score)
- Aggressive when at low HP

**PRIORITIZE_DAMAGE Flag** (Expert):
- Favors high power moves (+10 score)
- Penalizes status moves in some situations (-5 score)

## Strategy Tips

### Team Building
1. **Type Coverage**: Have answers to multiple types
2. **Role Balance**: Mix attackers, tanks, and speedsters
3. **Power Scaling**: Don't add Pokemon much weaker than your team
4. **Move Diversity**: Physical + Special + Status moves

### Battle Strategy
1. **Lead with Advantage**: Start with Pokemon that has type advantage
2. **Save Your Best**: Don't sacrifice strong Pokemon early
3. **Switch Wisely**: Switching wastes a turn, but saves HP
4. **Know When to Setup**: Stat-boosting moves require good timing
5. **Watch HP**: Heal before it's critical (under 50% HP)

### Advanced Tactics
1. **Speed Control**: Faster Pokemon control the battle flow
2. **Prediction**: CPU patterns become predictable at higher difficulties
3. **Status Effects**: Paralysis, poison, and burn are very powerful
4. **Setup Sweeping**: Boost stats, then sweep the team
5. **Resource Management**: PP is limited - don't spam your best move

## Team Compositions

Opponents use different team patterns:

### Balanced
- All Pokemon have similar strength
- Consistent challenge throughout
- Most common composition

### Glass Cannon
- 1 very strong Pokemon
- 2 medium Pokemon
- 3 weak Pokemon
- Dangerous if you can't stop the ace

### Ace Team
- 1-2 extremely strong Pokemon
- Rest are medium strength
- Focus on taking down the ace early

### Swarm
- All Pokemon are weaker than normal
- Strength in numbers
- Good for quick battles

## Power Cap System

Pokemon have maximum move power based on level:
- **Level 1-10**: 40-60 power moves
- **Level 11-20**: 50-80 power moves
- **Level 21-40**: 60-100 power moves
- **Level 41-60**: 70-120 power moves
- **Level 61+**: Up to 150 power moves

This prevents low-level Pokemon from one-shotting everything!

## Archetype System

Pokemon are assigned roles based on stats:

1. **Physical Attacker**: High Attack, learns physical moves
2. **Special Attacker**: High Sp. Attack, learns special moves
3. **Tank**: High HP and defenses, learns defensive moves
4. **Glass Cannon**: High offense, low defense
5. **Speedster**: High Speed, learns priority/setup moves
6. **Mixed Attacker**: Balanced Attack/Sp. Attack
7. **Wall**: Very high defenses, learns support moves

## Tips for Long Runs

1. **Early Game (Rounds 1-3)**:
   - Focus on building a solid core team
   - Take new Pokemon if they improve type coverage
   - Don't be afraid to switch often

2. **Mid Game (Rounds 4-7)**:
   - Optimize your team of 6 Pokemon
   - Be more selective with rewards
   - Start predicting CPU patterns

3. **Late Game (Rounds 8+)**:
   - Perfect your battle strategy
   - Every decision matters
   - Consider ending your run to save a good record

4. **Know When to Quit**:
   - Quitting after a win saves your streak
   - Sometimes it's better to preserve a good record
   - You can always start a new run

## Game Systems Reference

### Turn Resolution Order
1. **Priority Moves**: Higher priority goes first
2. **Speed Comparison**: Faster Pokemon goes first
3. **Random**: Tied speed = 50/50

### Damage Formula (Simplified)
```
Base Damage = ((2 * Level / 5 + 2) * Power * Attack / Defense / 50 + 2)
Random Factor: 0.85x - 1.0x
STAB: 1.5x if move matches Pokemon type
Type Effectiveness: 2x, 1x, 0.5x, or 0x
```

### Faint Mechanics
- Pokemon at 0 HP faints
- Must switch to another Pokemon
- Fainted Pokemon can't be used again this battle
- Battle ends when all Pokemon on one side have fainted

## Demo Mode

Want to see the systems in action without playing?
```bash
python demo_game.py
```

This runs an automated demonstration showing:
- Starter selection
- Opponent generation
- CPU AI decision-making
- Difficulty scaling
- Reward system
- Team compositions

## Files Reference

### Main Files
- `main.py` - Main game loop (play here!)
- `demo_game.py` - Automated demo
- `data/pokemon_battle.db` - Pokemon and move database

### Systems
- `models/team_generation.py` - Team building and scaling
- `models/cpu.py` - CPU AI with Generation 4 rules
- `models/turn_logic.py` - Battle turn system
- `models/Pokemon.py` - Pokemon class
- `models/Move.py` - Move class

### Repositories
- `src/repositories.py` - Database access layer
- `src/database.py` - Database initialization

## Troubleshooting

**Game won't start:**
- Make sure you're in the correct directory
- Check Python is installed: `python --version`
- Install dependencies if needed

**Battles feel too easy/hard:**
- Early rounds are deliberately easier
- Difficulty scales significantly after round 5
- Try different team compositions

**Want to see move details:**
- Check `data/pokemon_battle.db` in a SQLite viewer
- 428 moves available
- 111 unique effects

## Credits

Built with:
- **Database**: SQLite with 151 Gen 1 Pokemon, 428 moves
- **AI System**: Generation 4 Trainer AI rules
- **Team Generation**: TSB-based scaling system
- **Archetypes**: 7 role-based playstyles
- **Power Caps**: Level-based move restrictions

---

**Good luck, Trainer! How many rounds can you conquer?**

