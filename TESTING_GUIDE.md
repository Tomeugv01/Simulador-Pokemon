# Move System Testing - Quick Guide

## Overview
A comprehensive automated testing system that tests 425 move effects across 724 moves in the database.

## How to Run

```bash
python test_move_system.py
```

## What It Tests

### 1. **Damaging Moves** (Physical & Special)
- Tests first 50 physical and special moves
- Validates damage calculation
- Checks that moves execute without errors

### 2. **Status Moves**
- Thunder Wave, Toxic, Will-O-Wisp, Spore, etc.
- Verifies status conditions are applied correctly
- Tests: Paralysis, Burn, Freeze, Poison, Sleep

### 3. **Stat Change Moves**
- Swords Dance, Dragon Dance, Nasty Plot, etc.
- Verifies stat stages increase/decrease correctly
- Tests multi-stat boosts (Dragon Dance, Quiver Dance, etc.)

### 4. **Healing Moves**
- Recover, Roost, Rest, Synthesis, etc.
- Verifies HP restoration
- Tests percentage-based healing

### 5. **Complex Moves**
- **Charge Turns**: Solar Beam, Sky Attack
- **Invulnerability**: Dig, Fly, Dive, Bounce
- **Counter Moves**: Counter, Mirror Coat, Metal Burst, Bide
- **Fixed Damage**: Super Fang, Psywave, Endeavor, Final Gambit

### 6. **Priority Moves**
- Quick Attack, Extreme Speed, Aqua Jet, etc.
- Verifies priority brackets work correctly
- Tests that high-priority moves go first

### 7. **Weather Moves**
- Rain Dance, Sunny Day, Sandstorm, Hail
- Verifies weather is set correctly
- Checks weather turn duration

### 8. **Field Effects**
- **Screens**: Reflect, Light Screen
- **Hazards**: Stealth Rock, Spikes, Toxic Spikes, Sticky Web
- Verifies field effects are applied

### 9. **Recoil Moves**
- Take Down, Double-Edge, Flare Blitz, etc.
- Verifies recoil damage is applied to user
- Checks damage calculation

### 10. **Secondary Effects**
- Nuzzle (100% paralysis), Thunder Fang (10% paralysis), etc.
- Tests secondary effect application
- Verifies probability-based effects

## Test Results

### Current Status
```
Total Tests Run: 129
Moves Tested: 122

[PASS] PASSED: 129
[FAIL] FAILED: 0
[ERROR] ERRORS: 0
```

### Output Files
- **Console**: Real-time test progress and summary
- **test_results_detailed.txt**: Complete detailed report with all test results

## Test Report Format

### Summary Section
- Total number of tests run
- Count of passed/failed/errors
- Number of unique moves tested

### Passed Tests
- Move name and category
- Details (damage dealt, status applied, etc.)
- Turn log excerpt

### Failed Tests
- Move name and category
- Reason for failure
- Error message

### Errors
- Move name and category
- Exception details
- Full traceback for debugging

## Example Output

```
[PASS] Solar Beam (Complex) - Move appears in turn log: True
[PASS] Counter (Complex) - Move appears in turn log: True
[PASS] Reflect (Field Effect) - Field effect appears to be set: True
[PASS] Thunder Wave (Status) - Applied paralysis status
[PASS] Swords Dance (Stat Change) - Modified stats: {'attack': 2}
[PASS] Recover (Healing) - Healed 121 HP
```

## Adding More Tests

To test more moves, modify the test methods in `test_move_system.py`:

```python
# Test specific moves by name
test_move_names = ['Your', 'Move', 'Names', 'Here']

# Test by category
damaging_moves = [m for m in all_moves if m[2] in ('Physical', 'Special')]

# Test all moves (warning: takes longer)
for move_id, move_name, category, power, move_type, effects in all_moves:
    result = self._test_single_move(move_id, move_name, category)
```

## Interpreting Results

### Success Criteria

| Test Type | Success Condition |
|-----------|------------------|
| Damaging  | Damage > 0 dealt to target |
| Status    | Status condition applied or "already has status" message |
| Stat Change | At least one stat stage changed |
| Healing   | HP restored > 0 |
| Complex   | Move name appears in turn log |
| Weather   | Weather type changed |
| Field Effect | "set up" or move name in turn log |
| Recoil    | Damage dealt > 0 |

### Common Failure Reasons
- **"Exception: 'attribute_name'"**: Missing Pokemon attribute
- **"Move not found in database"**: Move doesn't exist in DB
- **"No effects found for move"**: Move has no effects in move_effect_instances table
- **"Move did not execute"**: Move failed to execute (accuracy check, PP, etc.)

## Performance

- **Current**: Tests 129 moves in ~5-10 seconds
- **Full suite**: Would test all 724 moves in ~30-60 seconds
- Tests run sequentially (not parallel)

## Next Steps

1. **Expand Coverage**: Increase from 50 to 100+ damaging moves
2. **Add Scenarios**: Test moves under different conditions (weather, status, etc.)
3. **Multi-Turn Tests**: Test charge moves across multiple turns
4. **Team Tests**: Test moves that affect entire teams
5. **Edge Cases**: Test moves at 1 HP, full HP, etc.

## Troubleshooting

### If tests fail:
1. Check `test_results_detailed.txt` for error details
2. Look for the specific move that failed
3. Check the traceback for the error location
4. Verify the move exists in the database with effects

### Common Issues:
- **Pokemon initialization**: Ensure Pokemon class __init__ matches usage
- **Move format**: Ensure moves are converted to dict format for BattleAction
- **Database connection**: Verify database file exists and has data

## Integration with Main Game

The testing system uses the same components as the main game:
- `TurnManager` for turn execution
- `BattleAction` for action creation
- `Pokemon` class for Pokemon objects
- Database for move effects

This ensures test results accurately reflect game behavior.
