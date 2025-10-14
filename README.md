# Battle System – Simple Explanation for Everyone

In this game, each run is a **turn-based battle adventure** where you and your opponents use teams of creatures called **Pokémon**, each with their own stats and attacks.  
The goal is to **progress through a series of battles**, growing stronger and building the best possible team before facing the **final boss**.

---

## How a Battle Works

Each battle happens in **turns**, where **you and your opponent** choose a move for your Pokémon.

1. **Speed determines who attacks first.**  
   The Pokémon with the highest speed acts first in the turn.

2. **Moves cause damage or effects.**  
   Some attacks reduce the opponent’s health, others can boost your stats, heal you, or inflict status conditions such as paralysis or confusion.

3. **Types matter.**  
   Every Pokémon and move has a **type** (fire, water, grass, etc.).  
   Some types are stronger against others: for example, water beats fire.

4. **The last team standing wins.**  
   When all of a player’s Pokémon have fainted, the other wins the battle.

---

## What Makes This System Special

While it looks like a classic turn-based system, the core of the project lies in **how teams are generated and evolve** throughout the run.

### Random but Balanced Teams

- At the start, the player receives a **random team**, but only from Pokémon within a moderate power range.  
- Opponents also get randomly generated teams, but **they get progressively stronger** after each battle.  
- The **difficulty is calculated automatically** based on the total sum of a team’s stats (attack, defense, speed, etc.).

### Strategic Progression

After each victory, the player can **choose one improvement**:

- **Add a new Pokémon to their team.**
- **Replace one of their current moves.**
- **(Later on)**, **obtain a special item.**

This forces the player to **choose their growth path**:  
Should they become stronger with new Pokémon or more flexible with better moves?

### Adaptive Enemy AI

Enemies don’t just get stronger – they also get **smarter** as you progress.  
Early opponents may act randomly, but higher-level ones will:

- Take advantage of type matchups.
- Switch Pokémon strategically.
- Use support or healing moves effectively.

---

## How Moves Are Selected

Each Pokémon has 4 moves.  
The moves they learn depend on their **combat archetype**, which the system determines automatically from their stat distribution.

For example:

- A Pokémon with high physical attack is a **“physical fighter”** and will get powerful contact-based moves.  
- One with high defense and HP is a **“tank”**, with slower but more durable attacks.  
- If a Pokémon has balanced stats across categories, it may draw moves from multiple archetypes, making it less predictable.

---

## Final Goal

The player progresses through increasingly challenging battles until facing the **final boss**.  
The boss has a **unique and pre-defined team**, not a random one, designed to deliver a **fair but challenging fight**.

Defeating the boss completes the run and may unlock **harder modes or new gameplay options**.

---

## In Summary

This battle system combines:

- **Strategy** (types, moves, turn order).  
- **Controlled randomness** (procedural team generation with balance).  
- **Meaningful progression** (player choices shape their power).  
- **Replayability** (every run feels different).
