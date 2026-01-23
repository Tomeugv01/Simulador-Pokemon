# Ability System Implementation

## Overview

Added complete ability system support to the Pokemon Battle Simulator database, including:
- **124 abilities** from Generations 1-4
- Database tables for abilities and Pokemon-ability mappings
- Schema integration with existing database structure

## Database Changes

### New Tables Created

#### 1. `abilities` Table
```sql
CREATE TABLE abilities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    overworld_effect TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

Stores all 124 abilities with their:
- **name**: Ability name (e.g., "Blaze", "Torrent", "Overgrow")
- **description**: In-battle effect description
- **overworld_effect**: Out-of-battle effects (optional)

#### 2. `pokemon_abilities` Table
```sql
CREATE TABLE pokemon_abilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    slot INTEGER DEFAULT 1,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id) ON DELETE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES abilities(id) ON DELETE CASCADE,
    UNIQUE (pokemon_id, ability_id)
)
```

Junction table linking Pokemon to their abilities:
- **pokemon_id**: Reference to pokemon table
- **ability_id**: Reference to abilities table
- **is_hidden**: Whether this is a hidden ability (for future use)
- **slot**: Ability slot number (1, 2, or 3 for hidden)

## Abilities Implemented

### Starter Abilities
- **Blaze**: Fire starters (Charmander line, Cyndaquil line, etc.)
- **Torrent**: Water starters (Squirtle line, Totodile line, etc.)
- **Overgrow**: Grass starters (Bulbasaur line, Chikorita line, etc.)

### Weather Abilities
- **Drizzle**: Summons rain (Kyogre)
- **Drought**: Summons sun (Groudon)
- **Sand Stream**: Summons sandstorm (Tyranitar, Hippowdon)
- **Snow Warning**: Summons hail (Snover, Abomasnow)

### Immunity Abilities
- **Levitate**: Immune to Ground moves (49 Pokemon)
- **Wonder Guard**: Only damaged by super effective moves (Shedinja)
- **Flash Fire**: Immune to Fire, powers up Fire moves
- **Volt Absorb**: Heals when hit by Electric
- **Water Absorb**: Heals when hit by Water

### Stat Boost Abilities
- **Huge Power/Pure Power**: Doubles Attack
- **Speed Boost**: Speed increases each turn
- **Adaptibility**: STAB bonus increased
- **Guts**: Attack increases when statused

### Contact Abilities
- **Static**: 30% paralyze on contact
- **Flame Body**: 30% burn on contact
- **Poison Point**: 30% poison on contact
- **Rough Skin**: Damages attacker on contact

### And 100+ More!

See [abilities_data_export.py](abilities_data_export.py) for complete list.

## Files Modified

### 1. [database.py](src/database.py)
- Added `abilities` table creation
- Added `pokemon_abilities` table creation

### 2. [add_pokemon_data.py](src/add_pokemon_data.py)
- Added `_insert_abilities()` method
- Integrated ability insertion into `initialize_pokemon_data()`

### 3. New Files
- **abilities_data_export.py** - Complete ability data (124 abilities)

## Current Status

✅ **Completed:**
- Database schema for abilities
- All 124 ability definitions extracted
- Ability insertion logic

⚠️ **To Do:**
- Map Pokemon to their abilities (pokemon_abilities table population)
- Implement ability effects in battle system
- Add ability selection during Pokemon creation

## Next Steps

### 1. Populate Pokemon-Ability Mappings

You'll need to create mappings from Pokemon names in the text file to Pokemon IDs in your database. Example:

```python
# From habilitats.txt:
# "Blaze" -> "Charmander Charmeleon Charizard Cyndaquil..."

POKEMON_ABILITIES_MAPPINGS = [
    (4, 9),  # Charmander -> Blaze
    (5, 9),  # Charmeleon -> Blaze  
    (6, 9),  # Charizard -> Blaze
    # ... etc
]
```

### 2. Implement Battle Effects

Add ability checking logic to your battle system:

```python
# Example in turn_logic.py
def calculate_damage(attacker, defender, move):
    damage = base_damage_calc(attacker, defender, move)
    
    # Check defender abilities
    if defender.ability == 'Filter' and is_super_effective(move, defender):
        damage *= 0.5
    
    if defender.ability == 'Levitate' and move.type == 'Ground':
        return 0
    
    # Check attacker abilities
    if attacker.ability == 'Adaptibility' and move.type in attacker.types:
        damage *= 2.0  # Instead of 1.5 for normal STAB
    
    return damage
```

### 3. Add to Pokemon Class

Update your Pokemon model to include abilities:

```python
# In models/Pokemon.py
class Pokemon:
    def __init__(self, ...):
        # ... existing code ...
        self.ability = self.get_ability_from_db()
    
    def get_ability_from_db(self):
        """Get this Pokemon's ability"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.name FROM abilities a
            JOIN pokemon_abilities pa ON a.id = pa.ability_id
            WHERE pa.pokemon_id = ? AND pa.is_hidden = FALSE
            ORDER BY pa.slot
            LIMIT 1
        ''', (self.id,))
        result = cursor.fetchone()
        return result[0] if result else None
```

## Usage

### Recreate Database with Abilities

```bash
py src/run.py
# Choose 'y' to reinitialize
```

The database will now include:
- All existing tables (types, moves, pokemon, etc.)
- New `abilities` table with 124 abilities
- New `pokemon_abilities` table (empty until you add mappings)

### Query Abilities

```python
import sqlite3

conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

# Get all abilities
cursor.execute("SELECT * FROM abilities ORDER BY name")
abilities = cursor.fetchall()

# Get a specific ability
cursor.execute("SELECT * FROM abilities WHERE name = ?", ('Blaze',))
blaze = cursor.fetchone()

# Get Pokemon with a specific ability (after mappings added)
cursor.execute('''
    SELECT p.name FROM pokemon p
    JOIN pokemon_abilities pa ON p.id = pa.pokemon_id
    JOIN abilities a ON pa.ability_id = a.id
    WHERE a.name = ?
''', ('Levitate',))
levitators = cursor.fetchall()
```

## Testing

Test the database creation:

```bash
py check_tables.py
```

Should show:
- `abilities` table with 124 records
- `pokemon_abilities` table with 0 records (until you add mappings)

## Notes

- The `pokemon_abilities` table uses a junction pattern because Pokemon can have multiple abilities (1-3 typically)
- `is_hidden` flag reserved for hidden abilities (like Speed Boost on Blaziken)
- `slot` indicates which ability slot (1 = first ability, 2 = second ability, 3 = hidden)
- All ability data extracted from your habilitats.txt file
- Abilities are Gen 1-4 compatible with your Pokemon database (Gen 1-4)

## Future Enhancements

1. **Hidden Abilities**: Add hidden ability support (Gen 5+)
2. **Ability Changes**: Some Pokemon gained new abilities in later generations
3. **Mega Evolution Abilities**: Mega Pokemon have different abilities
4. **Ability Popup**: Implement ability capsules for switching
5. **Ability Animations**: Add visual effects for ability triggers
