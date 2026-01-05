# Quick Reference Guide

## 🎮 How to Play

```bash
python main.py
```

## 📋 Quick Commands

| Action | Command |
|--------|---------|
| Play game | `python main.py` |
| Watch demo | `python demo_game.py` |
| Read guide | Open `GAME_GUIDE.md` |
| Check architecture | Open `ARCHITECTURE.md` |

## 🎯 Gameplay Loop

1. **Choose 3 Starters** (from 9 options)
2. **Battle Opponent** (CPU AI)
3. **Win → Level Up & Evolve** (gain 1-3 levels, stats increase)
4. **Get Rewards** (new Pokemon, continue, or quit)
5. **Next Round** (harder opponent)
6. **Repeat** until defeat

## 💡 Quick Tips

- **Type Advantage** = 2x damage (Water beats Fire)
- **Speed** = Who goes first
- **TSB** = Total stats (higher = stronger)
- **Power Caps** = Low-level Pokemon can't learn overpowered moves
- **Level Up** = Gain 1-3 levels per win (stats increase!)
- **Evolution** = Big stat boost when you choose to evolve

## 📊 Difficulty Progression

| Round | Player Level | Opponent Level | Team Size | AI |
|-------|--------------|----------------|-----------|-----|
| 1 | 5-6 | ~7 | 3 | Easy |
| 3 | 9-10 | ~14 | 3-4 | Normal |
| 5 | 13-15 | ~20 | 4 | Normal |
| 10 | 25-30 | ~55 | 5 | Hard |
| 15 | 40-50 | ~100 | 6 | Expert |

## 🤖 CPU AI Levels

- **Easy**: Avoids obvious mistakes
- **Normal**: Considers type effectiveness  
- **Hard**: Manages HP strategically
- **Expert**: Uses all tactics

## 📁 Important Files

| File | Purpose |
|------|---------|
| `main.py` | Play the game |
| `demo_game.py` | Automated demo |
| `test_level_progression.py` | Test level-up & evolution |
| `GAME_GUIDE.md` | Full instructions |
| `LEVEL_PROGRESSION.md` | Level system details |
| `README_NEW.md` | Project overview |
| `ARCHITECTURE.md` | System design |
| `PROJECT_SUMMARY.md` | What we built |

## 🔑 Key Concepts

**TSB (Total Stat Budget)**
- Sum of all 6 stats (HP + Atk + Def + SpA + SpD + Spe)
- Used to balance team strength
- Opponents scale ~30 TSB per round

**Archetypes** (7 types)
- Physical Attacker, Special Attacker, Tank
- Glass Cannon, Speedster, Mixed Attacker, Wall
- Determines move selection

**Power Caps**
- Level 5: Max 40-50 power moves
- Level 20: Max 80-90 power moves
- Level 50: Max 110-125 power moves

**Team Compositions**
- Balanced: All similar strength
- Glass Cannon: 1 strong ace
- Ace Team: 1-2 very strong
- Swarm: All weaker, more numbers

## 🎓 Battle Strategy

1. **Lead with type advantage**
2. **Switch before fainting** (if possible)
3. **Save your strongest** for late battle
4. **Watch HP percentages** (<30% = critical)
5. **Predict CPU patterns** (easier at higher difficulties)

## 📈 Stats Explained

| Stat | Effect |
|------|--------|
| HP | Health (higher = survive longer) |
| Attack | Physical move damage |
| Defense | Physical damage resistance |
| Sp. Attack | Special move damage |
| Sp. Defense | Special damage resistance |
| Speed | Turn order (higher goes first) |

## 🔢 Type Effectiveness

**Super Effective (2x damage)**
- Water → Fire, Rock, Ground
- Fire → Grass, Ice, Bug, Steel
- Grass → Water, Rock, Ground
- Electric → Water, Flying
- Ice → Grass, Ground, Flying, Dragon

**Not Very Effective (0.5x damage)**
- Reverse of super effective
- Example: Fire → Water (0.5x)

**Immune (0x damage)**
- Normal/Fighting → Ghost
- Ghost → Normal
- Electric → Ground
- Psychic → Dark
- Ground → Flying

## 🏆 Win Conditions

**Victory**: Defeat all opponent Pokemon
**Defeat**: All your Pokemon faint
**Forfeit**: Choose to quit (saves run)

## 💰 Reward Options

After winning a battle:
1. **Level Up!** Your team gains 1-3 levels (automatic)
2. **Evolution Choices** (if Pokemon can evolve)
3. **Add New Pokemon** (if team < 6)
4. **Continue** (proceed to next round)
5. **End Run** (save your streak)

Team is **fully healed** after each battle!

## 🛠️ Technical Info

- **Language**: Python 3.x
- **Database**: SQLite
- **Pokemon**: 151 (Gen 1)
- **Moves**: 428 (no duplicates)
- **Effects**: 111 (unique)
- **Types**: 18 (complete)

## 📞 Need Help?

1. Read `GAME_GUIDE.md` for detailed instructions
2. Run `demo_game.py` to see systems in action
3. Check `ARCHITECTURE.md` for technical details
4. Review `PROJECT_SUMMARY.md` for feature list

## 🎉 Have Fun!

**Goal**: Achieve the longest win streak possible!

Remember: One loss ends your run, so play strategically! 🏆
