# Status Move Refactoring - Data-Driven Approach

## Overview
Refactored the status move handling system in `turn_logic.py` to be database-driven instead of hardcoded, making it more maintainable and scalable.

## Problem
Previously, adding a new move to the database required also adding hardcoded logic in `_handle_status_move()`:
```python
# OLD APPROACH - Hardcoded
if 'Iron Defense' in move_name:
    user.modify_stat_stage('defense', 2)
    self._log(f"{user.name}'s Defense sharply rose!")
elif 'Amnesia' in move_name:
    user.modify_stat_stage('sp_defense', 2)
    # ... 20+ more hardcoded move checks
```

This meant:
- Every new move required code changes
- Not leveraging existing database structure
- Difficult to maintain and test
- Prone to errors and inconsistencies

## Solution
Created a generic, data-driven system that reads move effects from the database and applies them based on `effect_type`:

### New Architecture

1. **Effect Query System**
   - `_get_move_effects(move)`: Queries database for move's effects
   - Returns list of effects with structured data

2. **Generic Effect Application**
   - `_apply_single_effect()`: Central dispatcher for all effect types
   - Checks probability and effect target
   - Routes to specific handlers based on `effect_type`

3. **Effect Type Handlers**
   Each handler reads from database fields:

   - **`_apply_stat_change_effect()`**
     - Reads: `stat_to_change`, `stat_change_amount`
     - Handles: Single stat changes, multi-stat changes, "All" stats
     - Generates appropriate messages ("sharply rose" vs "rose")

   - **`_apply_status_effect()`**
     - Reads: `status_condition`
     - Maps database names to Pokemon status names
     - Checks if Pokemon can be statused
     - Generates contextual messages

   - **`_apply_heal_effect()`**
     - Reads: `heal_percentage`
     - Handles both drain (damage-based) and direct heals
     - Distinguishes between "drained" vs "restored" messages

   - **`_apply_weather_effect()`**
     - Reads: `weather_type`
     - Sets battle weather conditions

   - **`_apply_field_effect()`**
     - Reads: `field_condition`
     - Sets up field effects (Stealth Rock, etc.)

   - **`_apply_other_effect()`**
     - Handles special cases (Protect, etc.)

### Database Fields Used

From `move_effects` table:
- `effect_type`: STATUS | STAT_CHANGE | HEAL | WEATHER | FIELD_EFFECT | OTHER
- `status_condition`: Burn | Paralysis | Freeze | Poison | Sleep | Confusion
- `stat_to_change`: Attack | Defense | SpAttack | SpDefense | Speed | Accuracy | Evasion | All
- `stat_change_amount`: Integer (-6 to +6)
- `heal_percentage`: Percentage (0-100)
- `weather_type`: Rain | Sun | Sandstorm | Hail
- `field_condition`: Stealth Rock | Spikes | etc.
- `effect_target`: User | Target
- `probability`: Chance to activate (0-100)

## Example

**Database Entry:**
```
effect_name: 'Raise Defense 2'
effect_type: 'STAT_CHANGE'
stat_to_change: 'Defense'
stat_change_amount: 2
effect_target: 'User'
```

**Automatic Result:**
```python
# No code needed - database handles it
pokemon.modify_stat_stage('defense', 2)
self._log(f"{pokemon.name}'s Defense sharply rose!")
```

## Benefits

### ✅ Maintainability
- Single source of truth (database)
- No code changes for new moves
- Consistent behavior across all moves

### ✅ Scalability
- Easy to add new effect types
- Supports complex multi-effect moves
- Probability-based effects built-in

### ✅ Testability
- Data-driven = easier to test
- Can test effect system independently
- Database changes don't require code testing

### ✅ Consistency
- All moves use same effect application logic
- Stat change messages automatically correct ("sharply" for ±2+)
- Status condition handling unified

## Integration with Existing Systems

### Drain Moves
Previously hardcoded drain move list now uses `HEAL` effect type:
```python
# OLD: Hardcoded list
drain_moves = ['Absorb', 'Mega Drain', 'Giga Drain', ...]

# NEW: Database-driven
effect_type: 'HEAL'
heal_percentage: 50  # or 75 for Giga Drain
```

### Damage Move Effects
Secondary effects on damaging moves also use this system:
```python
# Example: Thunder with 10% paralysis chance
effect_type: 'STATUS'
status_condition: 'Paralysis'
probability: 10
effect_target: 'Target'
```

## Migration Path

### Phase 1: Core Refactoring ✅ COMPLETE
- Refactored `_handle_status_move()` to be data-driven
- Integrated drain moves into effect system
- Created generic effect application methods

### Phase 2: Further Opportunities 🔄 TODO
Identified similar hardcoded patterns that could benefit:
- Type effectiveness (currently hardcoded dict)
- Ability effects (could be database-driven)
- Item effects (could use similar pattern)

### Phase 3: Database Population
- Ensure all moves have proper effect entries
- Validate effect data completeness
- Test edge cases

## Technical Details

### Files Modified
- `models/turn_logic.py`: Complete refactoring (1055 lines)
  - Added `MoveRepository` import
  - Added `move_repo` to `__init__`
  - Created 7 new effect handler methods
  - Removed ~80 lines of hardcoded move checks

### Dependencies
- `repositories.MoveRepository`: For querying move effects
- Database tables: `moves`, `move_effects`, `move_effect_instances`

### Error Handling
- Graceful fallback if database unavailable
- Effect probability checks
- Status immunity checks
- HP boundary validations

## Usage Examples

### Adding a New Stat-Boosting Move
```sql
-- Database only - no code changes needed!
INSERT INTO move_effects VALUES (
    'Raise SpAtk 3',
    'Drastically raises Special Attack',
    'STAT_CHANGE',
    'None',
    'SpAttack',
    3,
    0, 0, 0,
    NULL, NULL,
    'User'
);
```

### Adding a Multi-Stat Move
```sql
-- Example: Cotton Guard (+3 Defense)
INSERT INTO move_effects VALUES (
    'Raise Defense 3',
    'Drastically raises Defense',
    'STAT_CHANGE',
    'None',
    'Defense',
    3,
    0, 0, 0,
    NULL, NULL,
    'User'
);
```

### Adding a Complex Move
```sql
-- Example: Shell Smash (multiple stat changes)
-- Just add multiple effect instances to the move!
-- Effect 1: Lower Defense -1
-- Effect 2: Lower SpDefense -1
-- Effect 3: Raise Attack +2
-- Effect 4: Raise SpAttack +2
-- Effect 5: Raise Speed +2
```

## Testing

### Verified Working
- ✅ Iron Defense (+2 Defense)
- ✅ Amnesia (+2 SpDefense)
- ✅ Agility (+2 Speed)
- ✅ Bulk Up (+1 Attack, +1 Defense)
- ✅ Coil (+1 Attack, +1 Defense, +1 Accuracy)
- ✅ Quiver Dance (+1 SpAttack, +1 SpDefense, +1 Speed)
- ✅ Shell Smash (-1 Defense, -1 SpDefense, +2 Attack, +2 SpAttack, +2 Speed)
- ✅ Drain moves (Absorb, Mega Drain, Giga Drain, etc.)

### To Test
- [ ] Status-inflicting moves (Thunder Wave, Toxic, Will-O-Wisp)
- [ ] Healing moves (Recover, Roost, etc.)
- [ ] Weather-setting moves (Rain Dance, Sunny Day)
- [ ] Protection moves (Protect, Detect)
- [ ] Secondary effect moves (Thunder, Fire Blast)

## Future Enhancements

1. **Conditional Effects**: Effects that trigger only under certain conditions
2. **Target Selection**: More complex targeting (all opponents, all allies, etc.)
3. **Duration Effects**: Effects that last multiple turns
4. **Stackable Effects**: Effects that can stack (Toxic damage scaling)
5. **Effect Chains**: One effect triggering another

## Conclusion

This refactoring transforms the move system from hardcoded and brittle to data-driven and flexible. Adding new moves is now as simple as adding database entries, making the system significantly more maintainable and scalable for future development.

**No more code changes needed for new moves!** 🎉
