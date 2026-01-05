"""
Move Effect classes for Pokemon battle system.
Defines all effect types and their functionality based on database definitions.
"""

import random
from enum import Enum


class EffectType(Enum):
    """Types of move effects"""
    STATUS = "STATUS"
    STAT_CHANGE = "STAT_CHANGE"
    HEAL = "HEAL"
    DAMAGE_MODIFIER = "DAMAGE_MODIFIER"
    FIELD_EFFECT = "FIELD_EFFECT"
    WEATHER = "WEATHER"
    RECOIL = "RECOIL"
    OTHER = "OTHER"


class EffectTarget(Enum):
    """Targets for effects"""
    USER = "User"
    TARGET = "Target"
    ALL_POKEMON = "AllPokemon"
    USER_SIDE = "UserSide"
    TARGET_SIDE = "TargetSide"
    FIELD = "Field"


class TriggerCondition(Enum):
    """When an effect triggers"""
    ALWAYS = "Always"
    ON_HIT = "OnHit"
    ON_CRIT = "OnCrit"
    IF_SECONDARY = "IfSecondary"
    IF_MISS = "IfMiss"


class MoveEffect:
    """
    Base class for all move effects.
    Represents a single effect that can be applied by a move.
    """
    
    def __init__(self, effect_data):
        """
        Initialize a move effect from database data.
        
        Args:
            effect_data (dict): Effect data with keys matching database columns
        """
        self.name = effect_data.get('effect_name', '')
        self.description = effect_data.get('description', '')
        self.effect_type = EffectType(effect_data.get('effect_type', 'OTHER'))
        self.target = EffectTarget(effect_data.get('effect_target', 'Target'))
        self.probability = effect_data.get('probability', 100)
        self.triggers_on = TriggerCondition(effect_data.get('triggers_on', 'OnHit'))
        
        # Specific effect properties
        self.status_condition = effect_data.get('status_condition', 'None')
        self.stat_to_change = effect_data.get('stat_to_change')
        self.stat_change_amount = effect_data.get('stat_change_amount', 0)
        self.heal_percentage = effect_data.get('heal_percentage', 0)
        self.heal_fixed_amount = effect_data.get('heal_fixed_amount', 0)
        self.recoil_percentage = effect_data.get('recoil_percentage', 0)
        self.weather_type = effect_data.get('weather_type', 'None')
        self.field_condition = effect_data.get('field_condition')
    
    def should_trigger(self, context=None):
        """
        Check if effect should trigger based on probability and conditions.
        
        Args:
            context (dict): Battle context (hit, crit, etc.). Optional, defaults to always hit.
        
        Returns:
            bool: True if effect should trigger
        """
        # Default context if none provided
        if context is None:
            context = {'hit': True, 'crit': False}
        
        # Check trigger condition
        if self.triggers_on == TriggerCondition.ON_HIT and not context.get('hit', False):
            return False
        if self.triggers_on == TriggerCondition.ON_CRIT and not context.get('crit', False):
            return False
        if self.triggers_on == TriggerCondition.IF_MISS and context.get('hit', False):
            return False
        
        # Check probability
        return random.randint(1, 100) <= self.probability
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Apply the effect. Override in subclasses.
        
        Args:
            user: Pokemon using the move
            target: Pokemon being targeted
            battle_state: Current battle state
            damage_dealt (int): Damage dealt by the move (for drain/recoil)
        
        Returns:
            dict: Result of applying the effect
        """
        raise NotImplementedError("Subclasses must implement apply()")
    
    def __repr__(self):
        return f"{self.name} ({self.effect_type.value}, {self.probability}%)"


class StatusEffect(MoveEffect):
    """Effect that applies a status condition"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Apply status condition to target.
        
        Returns:
            dict: {'success': bool, 'status': str, 'message': str}
        """
        if self.target == EffectTarget.USER:
            pokemon = user
        else:
            pokemon = target
        
        status = self.status_condition.lower()
        
        # Special handling for confusion (volatile status)
        if status == 'confusion':
            if not pokemon.confused:
                pokemon.confused = True
                pokemon.confusion_turns = random.randint(1, 4)  # 1-4 turns
                return {
                    'success': True,
                    'status': 'confusion',
                    'message': f"{pokemon.name} became confused!"
                }
            return {'success': False, 'status': 'confusion', 'message': f"{pokemon.name} is already confused!"}
        
        # Major status conditions (with sleep duration)
        duration = random.randint(1, 3) if status == 'sleep' else 0
        success = pokemon.apply_status(status, duration)
        if success:
            return {
                'success': True,
                'status': status,
                'message': f"{pokemon.name} was {status}ed!"
            }
        return {
            'success': False,
            'status': status,
            'message': f"{pokemon.name} couldn't be {status}ed!"
        }


class StatChangeEffect(MoveEffect):
    """Effect that modifies stat stages"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Modify stat stages.
        
        Returns:
            dict: {'success': bool, 'stat': str, 'change': int, 'message': str}
        """
        if self.target == EffectTarget.USER:
            pokemon = user
            target_name = "user"
        else:
            pokemon = target
            target_name = "target"
        
        stat = self.stat_to_change
        change = self.stat_change_amount
        
        # Handle "All" stats
        if stat == 'All':
            stats = ['attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
            results = []
            for s in stats:
                actual_change = pokemon.modify_stat_stage(s, change)
                if actual_change != 0:
                    results.append(f"{s}: {actual_change:+d}")
            
            if results:
                return {
                    'success': True,
                    'stat': 'all',
                    'change': change,
                    'message': f"{pokemon.name}'s stats changed: {', '.join(results)}"
                }
            return {
                'success': False,
                'stat': 'all',
                'change': 0,
                'message': f"{pokemon.name}'s stats can't change any further!"
            }
        
        # Convert database stat names to Pokemon.py format
        stat_name = stat.lower()
        if stat_name.startswith('sp') and stat_name != 'speed':
            stat_name = 'sp_' + stat_name[2:]  # SpAttack -> sp_attack, SpDefense -> sp_defense
        
        # Apply stat change
        actual_change = pokemon.modify_stat_stage(stat_name, change)
        
        if actual_change != 0:
            direction = "rose" if actual_change > 0 else "fell"
            degree = "sharply " if abs(actual_change) >= 2 else ""
            return {
                'success': True,
                'stat': stat_name,
                'change': actual_change,
                'message': f"{pokemon.name}'s {stat} {degree}{direction}!"
            }
        return {
            'success': False,
            'stat': stat_name,
            'change': 0,
            'message': f"{pokemon.name}'s {stat} won't go any {'higher' if change > 0 else 'lower'}!"
        }


class HealEffect(MoveEffect):
    """Effect that heals HP"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Heal HP.
        
        Returns:
            dict: {'success': bool, 'amount': int, 'message': str}
        """
        pokemon = user if self.target == EffectTarget.USER else target
        
        # Calculate heal amount
        if self.heal_percentage > 0:
            if "Drain" in self.name:
                # Drain effects heal based on damage dealt
                heal_amount = max(1, (damage_dealt * self.heal_percentage) // 100)
            else:
                # Regular heal based on max HP
                heal_amount = max(1, (pokemon.max_hp * self.heal_percentage) // 100)
        else:
            heal_amount = self.heal_fixed_amount
        
        # Special handling for status cure
        if "Cure" in self.name:
            if pokemon.status:
                old_status = pokemon.status
                pokemon.cure_status()
                return {
                    'success': True,
                    'amount': 0,
                    'message': f"{pokemon.name} was cured of {old_status}!"
                }
            return {
                'success': False,
                'amount': 0,
                'message': f"{pokemon.name} has no status to cure!"
            }
        
        # Apply healing
        healed = pokemon.heal(heal_amount)
        if healed > 0:
            return {
                'success': True,
                'amount': healed,
                'message': f"{pokemon.name} restored {healed} HP!"
            }
        return {
            'success': False,
            'amount': 0,
            'message': f"{pokemon.name}'s HP is already full!"
        }


class RecoilEffect(MoveEffect):
    """Effect that damages the user (recoil)"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Apply recoil damage to user.
        
        Returns:
            dict: {'success': bool, 'damage': int, 'message': str}
        """
        # Calculate recoil damage
        recoil_damage = max(1, (damage_dealt * self.recoil_percentage) // 100)
        
        # Apply damage
        actual_damage = user.take_damage(recoil_damage)
        
        return {
            'success': True,
            'damage': actual_damage,
            'message': f"{user.name} took {actual_damage} recoil damage!"
        }


class WeatherEffect(MoveEffect):
    """Effect that changes weather"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Set weather condition.
        
        Returns:
            dict: {'success': bool, 'weather': str, 'duration': int, 'message': str}
        """
        weather = self.weather_type
        duration = 5  # Standard weather duration
        
        # Set weather in battle state
        battle_state['weather'] = weather
        battle_state['weather_turns'] = duration
        
        messages = {
            'Sun': f"The sunlight turned harsh!",
            'Rain': f"It started to rain!",
            'Sandstorm': f"A sandstorm kicked up!",
            'Hail': f"It started to hail!"
        }
        
        return {
            'success': True,
            'weather': weather,
            'duration': duration,
            'message': messages.get(weather, f"Weather changed to {weather}!")
        }


class FieldEffect(MoveEffect):
    """Effect that sets field conditions (hazards, terrain, etc.)"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Set field condition.
        
        Returns:
            dict: {'success': bool, 'condition': str, 'message': str}
        """
        condition = self.field_condition
        side = 'target_side' if self.target == EffectTarget.TARGET_SIDE else 'user_side'
        
        # Initialize field conditions if not present
        if 'field_conditions' not in battle_state:
            battle_state['field_conditions'] = {
                'user_side': [],
                'target_side': []
            }
        
        # Add condition
        if condition not in battle_state['field_conditions'][side]:
            battle_state['field_conditions'][side].append(condition)
            
            messages = {
                'Spikes': f"Spikes were scattered on the ground!",
                'ToxicSpikes': f"Poison spikes were scattered on the ground!",
                'StealthRock': f"Pointed stones float in the air!",
            }
            
            return {
                'success': True,
                'condition': condition,
                'message': messages.get(condition, f"{condition} was set!")
            }
        
        return {
            'success': False,
            'condition': condition,
            'message': f"{condition} is already in effect!"
        }


class SpecialEffect(MoveEffect):
    """Effect for special mechanics (flinch, priority, protect, etc.)"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        Apply special effect.
        
        Returns:
            dict: Result varies by effect type
        """
        effect_name = self.name
        
        # Flinch
        if 'Flinch' in effect_name:
            target.flinched = True
            return {
                'success': True,
                'effect': 'flinch',
                'message': f"{target.name} flinched!"
            }
        
        # Protect
        if 'Protect' in effect_name:
            user.protected = True
            return {
                'success': True,
                'effect': 'protect',
                'message': f"{user.name} protected itself!"
            }
        
        # Multi-hit
        if 'Multi Hit' in effect_name:
            if '2-5' in effect_name:
                hits = random.choice([2, 2, 3, 3, 4, 5])  # Weighted towards 2-3
            elif '2' in effect_name:
                hits = 2
            elif '3' in effect_name:
                hits = 3
            else:
                hits = 1
            
            return {
                'success': True,
                'effect': 'multi_hit',
                'hits': hits,
                'message': f"Hit {hits} times!"
            }
        
        # Recharge turn
        if 'Recharge Turn' in effect_name:
            user.recharging = True
            return {
                'success': True,
                'effect': 'recharge',
                'message': f"{user.name} must recharge!"
            }
        
        # Trap
        if 'Trap' in effect_name:
            target.trapped = True
            if '4-5' in effect_name:
                target.trap_turns = random.randint(4, 5)
            else:
                target.trap_turns = random.randint(2, 5)
            return {
                'success': True,
                'effect': 'trap',
                'message': f"{target.name} was trapped!"
            }
        
        # Force switch
        if 'Force Switch' in effect_name:
            return {
                'success': True,
                'effect': 'force_switch',
                'message': f"{target.name} was forced to switch!"
            }
        
        # Switch out
        if 'Switch Out' in effect_name:
            return {
                'success': True,
                'effect': 'switch_out',
                'message': f"{user.name} switches out!"
            }
        
        # Self HP cost
        if 'Self HP Cost' in effect_name:
            cost = (user.max_hp * 50) // 100
            user.take_damage(cost)
            return {
                'success': True,
                'effect': 'hp_cost',
                'cost': cost,
                'message': f"{user.name} paid {cost} HP!"
            }
        
        # Force Berry
        if 'Force Berry' in effect_name:
            return {
                'success': True,
                'effect': 'force_berry',
                'message': f"All Pokemon ate their berries!"
            }
        
        # Remove item
        if 'Remove Item' in effect_name:
            return {
                'success': True,
                'effect': 'remove_item',
                'message': f"{target.name}'s item was removed!"
            }
        
        # Type changes (placeholder - would need type system)
        if 'Change Type' in effect_name:
            return {
                'success': True,
                'effect': 'type_change',
                'message': f"{target.name}'s type changed!"
            }
        
        # Substitute
        if 'Substitute' in effect_name:
            success = user.create_substitute()
            if success:
                return {
                    'success': True,
                    'effect': 'substitute',
                    'message': f"{user.name} created a substitute!"
                }
            return {
                'success': False,
                'effect': 'substitute',
                'message': f"{user.name} doesn't have enough HP!"
            }
        
        # Encore
        if 'Encore' in effect_name:
            target.encore = True
            target.encore_turns = 3
            target.encore_move = target.last_move_used
            return {
                'success': True,
                'effect': 'encore',
                'message': f"{target.name} received an encore!"
            }
        
        # Taunt
        if 'Taunt' in effect_name:
            target.taunted = True
            target.taunt_turns = 3
            return {
                'success': True,
                'effect': 'taunt',
                'message': f"{target.name} fell for the taunt!"
            }
        
        # Disable
        if 'Disable' in effect_name:
            target.disabled_move = target.last_move_used
            target.disable_turns = 4
            return {
                'success': True,
                'effect': 'disable',
                'message': f"{target.name}'s move was disabled!"
            }
        
        # Torment
        if 'Torment' in effect_name:
            target.tormented = True
            return {
                'success': True,
                'effect': 'torment',
                'message': f"{target.name} was subjected to torment!"
            }
        
        # Curse (Ghost-type)
        if 'Curse' in effect_name and 'Ghost' in effect_name:
            target.cursed = True
            cost = user.max_hp // 2
            user.take_damage(cost)
            return {
                'success': True,
                'effect': 'curse',
                'message': f"{user.name} cut its own HP and laid a curse on {target.name}!"
            }
        
        # Ingrain
        if 'Ingrain' in effect_name:
            user.ingrain = True
            return {
                'success': True,
                'effect': 'ingrain',
                'message': f"{user.name} planted its roots!"
            }
        
        # Aqua Ring
        if 'Aqua Ring' in effect_name:
            user.aqua_ring = True
            return {
                'success': True,
                'effect': 'aqua_ring',
                'message': f"{user.name} surrounded itself with a veil of water!"
            }
        
        # Embargo
        if 'Embargo' in effect_name:
            target.embargo = True
            target.embargo_turns = 5
            return {
                'success': True,
                'effect': 'embargo',
                'message': f"{target.name} can't use items anymore!"
            }
        
        # Heal Block
        if 'Heal Block' in effect_name:
            target.heal_block = True
            target.heal_block_turns = 5
            return {
                'success': True,
                'effect': 'heal_block',
                'message': f"{target.name} was prevented from healing!"
            }
        
        # Yawn
        if 'Yawn' in effect_name:
            target.yawn = True
            target.yawn_turns = 1  # Falls asleep next turn
            return {
                'success': True,
                'effect': 'yawn',
                'message': f"{target.name} grew drowsy!"
            }
        
        # Prevent Switching
        if 'Prevent Switching' in effect_name:
            target.trapped = True
            target.trap_turns = 999  # Indefinite until user switches
            return {
                'success': True,
                'effect': 'prevent_switch',
                'message': f"{target.name} can no longer escape!"
            }
        
        # Default for unhandled special effects
        return {
            'success': True,
            'effect': 'other',
            'message': f"{effect_name} activated!"
        }


class DamageModifierEffect(MoveEffect):
    """Effect that modifies damage calculation"""
    
    def __init__(self, effect_data):
        super().__init__(effect_data)
    
    def apply(self, user, target, battle_state, damage_dealt=0):
        """
        This effect modifies damage calculation, so it's applied differently.
        This method just stores metadata.
        
        Returns:
            dict: Metadata about the modifier
        """
        return {
            'success': True,
            'effect': 'damage_modifier',
            'modifier_type': self.name,
            'message': ''
        }
    
    def get_damage_multiplier(self, user, target, battle_state):
        """
        Calculate damage multiplier based on conditions.
        
        Returns:
            float: Damage multiplier
        """
        # HP Scaling High - more power at higher HP
        if 'HP Scaling High' in self.name:
            hp_ratio = user.current_hp / user.max_hp
            return 1.0 + (hp_ratio * 0.5)  # Up to 1.5x at full HP
        
        # Speed Dependent - double if user is faster
        if 'Speed Dependent' in self.name:
            if user.get_effective_stat('speed') > target.get_effective_stat('speed'):
                return 2.0
            return 1.0
        
        # Stat Boost Scaling - +20 power per stat boost
        if 'Stat Boost Scaling' in self.name:
            total_boosts = sum(max(0, stage) for stage in user.stat_stages.values())
            # Each boost adds ~15% power
            return 1.0 + (total_boosts * 0.15)
        
        # Pursuit Damage - double if target is switching
        if 'Pursuit Damage' in self.name:
            if battle_state.get('target_switching', False):
                return 2.0
            return 1.0
        
        # Default
        return 1.0


def create_effect_from_data(effect_data):
    """
    Factory function to create appropriate effect type from data.
    
    Args:
        effect_data (dict): Effect data from database
    
    Returns:
        MoveEffect: Appropriate effect subclass instance
    """
    effect_type = effect_data.get('effect_type', 'OTHER')
    
    if effect_type == 'STATUS':
        return StatusEffect(effect_data)
    elif effect_type == 'STAT_CHANGE':
        return StatChangeEffect(effect_data)
    elif effect_type == 'HEAL':
        return HealEffect(effect_data)
    elif effect_type == 'RECOIL':
        return RecoilEffect(effect_data)
    elif effect_type == 'WEATHER':
        return WeatherEffect(effect_data)
    elif effect_type == 'FIELD_EFFECT':
        return FieldEffect(effect_data)
    elif effect_type == 'DAMAGE_MODIFIER':
        return DamageModifierEffect(effect_data)
    elif effect_type == 'OTHER':
        return SpecialEffect(effect_data)
    else:
        return MoveEffect(effect_data)


def apply_move_effects(effects_list, user, target, battle_state=None, damage_dealt=0, context=None):
    """
    Convenience function to apply a list of effects in order.
    
    Args:
        effects_list (list): List of MoveEffect objects
        user: Pokemon using the move
        target: Pokemon being targeted
        battle_state (dict): Current battle state, optional (creates default if None)
        damage_dealt (int): Damage dealt by the move (for drain/recoil)
        context (dict): Battle context (hit, crit, etc.), optional
    
    Returns:
        list: List of result dictionaries from each effect that triggered
    """
    if battle_state is None:
        battle_state = {}
    
    if context is None:
        context = {'hit': True, 'crit': False}
    
    results = []
    for effect in effects_list:
        if effect.should_trigger(context):
            result = effect.apply(user, target, battle_state, damage_dealt)
            results.append(result)
    
    return results


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING MOVE EFFECTS")
    print("=" * 70)
    
    # Test status effect
    print("\n1. Testing Status Effect (Burn 30%)...")
    burn_effect_data = {
        'effect_name': 'Burn 30%',
        'description': '30% chance to inflict burn',
        'effect_type': 'STATUS',
        'status_condition': 'Burn',
        'probability': 30,
        'effect_target': 'Target',
        'triggers_on': 'OnHit'
    }
    burn_effect = create_effect_from_data(burn_effect_data)
    print(f"   Created: {burn_effect}")
    
    # Test stat change effect
    print("\n2. Testing Stat Change Effect (Raise Attack 2)...")
    stat_effect_data = {
        'effect_name': 'Raise Attack 2',
        'description': 'Sharply raises Attack',
        'effect_type': 'STAT_CHANGE',
        'stat_to_change': 'Attack',
        'stat_change_amount': 2,
        'probability': 100,
        'effect_target': 'User',
        'triggers_on': 'Always'
    }
    stat_effect = create_effect_from_data(stat_effect_data)
    print(f"   Created: {stat_effect}")
    
    # Test heal effect
    print("\n3. Testing Heal Effect (Heal 50%)...")
    heal_effect_data = {
        'effect_name': 'Heal 50%',
        'description': 'Heals user by 50% of max HP',
        'effect_type': 'HEAL',
        'heal_percentage': 50,
        'probability': 100,
        'effect_target': 'User',
        'triggers_on': 'Always'
    }
    heal_effect = create_effect_from_data(heal_effect_data)
    print(f"   Created: {heal_effect}")
    
    # Test weather effect
    print("\n4. Testing Weather Effect (Set Rain)...")
    weather_effect_data = {
        'effect_name': 'Set Rain',
        'description': 'Sets rain for 5 turns',
        'effect_type': 'WEATHER',
        'weather_type': 'Rain',
        'probability': 100,
        'effect_target': 'Field',
        'triggers_on': 'Always'
    }
    weather_effect = create_effect_from_data(weather_effect_data)
    print(f"   Created: {weather_effect}")
    
    print("\n" + "=" * 70)
    print("✅ All effect types created successfully!")
    print("=" * 70)
