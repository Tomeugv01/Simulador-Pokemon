# Missing Secondary Effects Analysis

## Test Results Summary
- **Total Tests**: 609
- **Passed**: 564 (92.6%)
- **Failed**: 45 (7.4%)
- **Errors**: 0

## Root Cause
Most failures show **0.0% trigger rate**, indicating these effects are **NOT IMPLEMENTED** in turn_logic.py, not that they have incorrect probabilities.

## Failed Effect Categories

### 1. FLINCH Effects (23 moves - 0% trigger rate)
**Issue**: Flinch effect is NOT implemented in turn_logic.py

Failed moves:
- Air Slash (30%)
- Bite (30%)
- Bone Club (10%)
- Dark Pulse (20%)
- Double Iron Bash (30%)
- Dragon Rush (20%)
- Fake Out (100%) ← Should work 100% of time!
- Headbutt (30%)
- Heart Stamp (30%)
- Hyper Fang (30%)
- Icicle Crash (30%)
- Iron Head (30%)
- Needle Arm (30%)
- Rock Slide (30%)
- Rolling Kick (30%)
- Sky Attack (30%)
- Stomp (30%)
- Waterfall (20%)
- Zen Headbutt (20%)
- Zing Zap (30%)

**Database Status**: ✅ Flinch effect exists in database (ID 80)
**Implementation Status**: ❌ NOT implemented in turn_logic.py

### 2. CONFUSION Effects (8 moves - 0% trigger rate)
**Issue**: Confusion effect is NOT implemented in turn_logic.py

Failed moves:
- Chatter (100%)
- Confusion (10%)
- Dizzy Punch (10%)
- Dynamic Punch (100%)
- Hurricane (30%)
- Petal Dance (10%)
- Psybeam (10%)
- Thrash (10%)

**Database Status**: ❌ Confusion not in status_condition CHECK constraint
**Implementation Status**: ❌ NOT implemented in turn_logic.py

### 3. STAT CHANGE Effects - Self Buffs (8 moves)
**Issue**: Self-targeting stat boosts from damaging moves not working

Failed moves:
- Ancient Power (10% - All stats +1)
- Diamond Storm (50% - Defense +2)
- Metal Claw (10% - Attack +1)
- Meteor Mash (20% - Attack +1)
- Ominous Wind (10% - All stats +1)
- Rage (10% - Attack +1)
- Silver Wind (10% - All stats +1)

**Pattern**: These boost the USER's stats, not the target's
**Issue**: turn_logic.py likely only applies stat changes to TARGET, not USER

### 4. LOW TRIGGER RATE (5 moves - 3.3% instead of 10%)
**Issue**: Partial implementation or detection problem

- Flash Cannon (10% SpDef down) - Only 3.3%
- Heat Wave (10% Burn) - Only 3.3%
- Ice Punch (10% Freeze) - Only 3.3%
- Play Rough (10% Attack down) - Only 3.3%
- Powder Snow (10% Freeze) - Only 3.3%

**Pattern**: All 10% probability moves showing ~3% trigger rate
**Possible Cause**: Probability check might be running but effect application failing sometimes

### 5. HIGH PROBABILITY FAILURES (2 moves)
**Issue**: Should be near 100% but showing ~50%

- Inferno (100% Burn) - Only 53.3%
- Zap Cannon (100% Paralysis) - Only 46.7%

**Pattern**: 100% probability moves only triggering ~50% of time
**Possible Cause**: Effect application failing after probability check passes

## What Needs to Be Implemented

### Priority 1: Flinch Mechanism
```python
# In turn_logic.py, after damage is dealt:
if flinch_effect and probability_check_passes:
    target.flinched = True  # Prevents target from moving THIS turn
    turn_log.append(f"{target.name} flinched!")
```

**Critical**: Flinch only works if applied BEFORE target acts in same turn
- Requires checking priority and speed order
- Target must not have acted yet
- Fake Out and others MUST work since they have high priority

### Priority 2: Confusion Status
```python
# Add to status_condition CHECK constraint in database:
# 'Confusion' needs to be valid status
# Implement confusion logic in turn_logic.py:
# - Pokemon has X% chance to hurt itself instead of using move
# - Lasts 1-4 turns
# - Can be cured by certain items/moves
```

### Priority 3: Self-Targeting Stat Boosts
```python
# In turn_logic.py effect application:
if effect_target == 'User':
    # Apply stat changes to USER (attacker)
    user.stat_stages[stat] += amount
elif effect_target == 'Target':
    # Apply stat changes to TARGET (defender)
    target.stat_stages[stat] += amount
```

### Priority 4: Fix Status Application
- Investigate why Inferno and Zap Cannon only work 50% of time
- Check if effect application is being blocked by existing status
- Verify probability rolls are working correctly

## Recommended Fix Order

1. **Add Flinch Implementation** (fixes 23 moves)
   - Biggest impact
   - Critical for gameplay (Fake Out is priority move)

2. **Add Confusion to Database & Implementation** (fixes 8 moves)
   - Requires database schema change
   - Important status condition

3. **Fix Self-Targeting Stat Boosts** (fixes 8 moves)
   - Modify effect_target handling

4. **Debug Status Application** (fixes 7 moves)
   - Investigate why 100% moves fail 50% of time
   - Check for blocking conditions

## Files to Modify

1. **src/database.py** (line ~79)
   - Add 'Confusion' to status_condition CHECK constraint
   
2. **models/turn_logic.py**
   - Add flinch mechanism (check before move execution)
   - Add confusion implementation (in status effect section)
   - Fix effect_target to support 'User' vs 'Target'
   - Debug status application for 100% probability moves

3. **models/Pokemon.py** (possibly)
   - Add `flinched` attribute if not present
   - Add confusion turn counter

## Expected Results After Fixes
- **Flinch fixes**: 564 + 20 = 584 passed (95.9%)
- **Confusion fixes**: 584 + 8 = 592 passed (97.2%)
- **Self-stat fixes**: 592 + 8 = 600 passed (98.5%)
- **Status debug**: 600 + 7 = 607 passed (99.7%)
- **Target**: 607/609 passed (99.7% success rate)

The 2 remaining failures would need individual investigation.
