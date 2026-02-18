"""
Pokemon Ability System
Comprehensive ability effect handlers for the battle system.
Covers all 195 abilities with proper trigger points and battle mechanics.
"""
import random

try:
    from constants import get_type_effectiveness as _const_type_eff
except ImportError:
    try:
        from models.constants import get_type_effectiveness as _const_type_eff
    except ImportError:
        _const_type_eff = None


# =============================================================================
# ABILITY CLASSIFICATION BY TRIGGER POINT
# =============================================================================

# Abilities that activate when the Pokemon switches in
SWITCH_IN_ABILITIES = {
    # Weather setters
    'Drought': 'weather_sun',
    'Drizzle': 'weather_rain',
    'Sand Stream': 'weather_sandstorm',
    'Snow Warning': 'weather_hail',
    'Desolate Land': 'weather_sun',      # Primal
    'Primordial Sea': 'weather_rain',    # Primal
    'Delta Stream': 'weather_strong_wind',
    # Stat modification on opponents
    'Intimidate': 'intimidate',
    # Terrain setters
    'Electric Surge': 'terrain_electric',
    'Grassy Surge': 'terrain_grassy',
    'Misty Surge': 'terrain_misty',
    'Psychic Surge': 'terrain_psychic',
    # Other switch-in
    'Trace': 'trace',
    'Download': 'download',
    'Anticipation': 'anticipation',
    'Forewarn': 'forewarn',
    'Frisk': 'frisk',
    'Air Lock': 'air_lock',
    'Cloud Nine': 'cloud_nine',
    'Pressure': 'pressure_announce',
    'Mold Breaker': 'mold_breaker_announce',
    'Turboblaze': 'mold_breaker_announce',
    'Teravolt': 'mold_breaker_announce',
    'Unnerve': 'unnerve',
    'Imposter': 'imposter',
    'Neutralizing Gas': 'neutralizing_gas',
}

# Abilities that modify the damage calculation (attacker side)
ATTACKER_DAMAGE_ABILITIES = {
    # Raw power multipliers
    'Huge Power': {'stat': 'attack', 'multiplier': 2.0},
    'Pure Power': {'stat': 'attack', 'multiplier': 2.0},
    'Hustle': {'stat': 'attack', 'multiplier': 1.5},
    'Flower Gift': {'stat': 'attack', 'multiplier': 1.5, 'condition': 'sun'},
    'Solar Power': {'stat': 'sp_attack', 'multiplier': 1.5, 'condition': 'sun'},
    'Plus': {'stat': 'sp_attack', 'multiplier': 1.5},
    'Minus': {'stat': 'sp_attack', 'multiplier': 1.5},
    
    # Conditional power boosts
    'Guts': {'stat': 'attack', 'multiplier': 1.5, 'condition': 'has_status'},
    'Toxic Boost': {'stat': 'attack', 'multiplier': 1.5, 'condition': 'poison'},
    'Flare Boost': {'stat': 'sp_attack', 'multiplier': 1.5, 'condition': 'burn'},
    'Defeatist': {'stat': 'both_attack', 'multiplier': 0.5, 'condition': 'low_hp'},
    
    # Move-type power boosts  
    'Blaze': {'type': 'Fire', 'multiplier': 1.5, 'condition': 'low_hp'},
    'Torrent': {'type': 'Water', 'multiplier': 1.5, 'condition': 'low_hp'},
    'Overgrow': {'type': 'Grass', 'multiplier': 1.5, 'condition': 'low_hp'},
    'Swarm': {'type': 'Bug', 'multiplier': 1.5, 'condition': 'low_hp'},
    
    # Category-specific boosts
    'Technician': {'max_bp': 60, 'multiplier': 1.5},
    'Iron Fist': {'flag': 'punch', 'multiplier': 1.2},
    'Strong Jaw': {'flag': 'bite', 'multiplier': 1.5},
    'Mega Launcher': {'flag': 'pulse', 'multiplier': 1.5},
    'Reckless': {'flag': 'recoil', 'multiplier': 1.2},
    'Tough Claws': {'flag': 'contact', 'multiplier': 1.3},
    'Sharpness': {'flag': 'slicing', 'multiplier': 1.5},
    
    # STAB modification
    'Adaptability': {'stab_boost': 2.0},  # STAB becomes 2x instead of 1.5x
    
    # Type-specific offensive boosts (sand/weather)
    'Sand Force': {'types': ['Rock', 'Ground', 'Steel'], 'multiplier': 1.3, 'condition': 'sandstorm'},
    
    # Critical hit boost handled in crit calc
    'Sniper': {'crit_multiplier': 2.25},  # Crit damage becomes 2.25x instead of 1.5x
    
    # Sheer Force: boost power but remove secondary effects
    'Sheer Force': {'multiplier': 1.3, 'removes_secondary': True},
    
    # Analytic: 1.3x if moving last
    'Analytic': {'multiplier': 1.3, 'condition': 'moved_last'},
    
    # Normalize: all moves become Normal type
    'Normalize': {'change_type': 'Normal'},
    'Pixilate': {'change_type': 'Fairy', 'from_type': 'Normal', 'multiplier': 1.2},
    'Refrigerate': {'change_type': 'Ice', 'from_type': 'Normal', 'multiplier': 1.2},
    'Aerilate': {'change_type': 'Flying', 'from_type': 'Normal', 'multiplier': 1.2},
    'Galvanize': {'change_type': 'Electric', 'from_type': 'Normal', 'multiplier': 1.2},
}

# Abilities that modify the damage calculation (defender side)
DEFENDER_DAMAGE_ABILITIES = {
    'Thick Fat': {'types': ['Fire', 'Ice'], 'multiplier': 0.5},
    'Heatproof': {'types': ['Fire'], 'multiplier': 0.5},
    'Dry Skin': {'types': ['Fire'], 'multiplier': 1.25},  # Takes MORE fire damage
    'Filter': {'condition': 'super_effective', 'multiplier': 0.75},
    'Solid Rock': {'condition': 'super_effective', 'multiplier': 0.75},
    'Prism Armor': {'condition': 'super_effective', 'multiplier': 0.75},
    'Multiscale': {'condition': 'full_hp', 'multiplier': 0.5},
    'Shadow Shield': {'condition': 'full_hp', 'multiplier': 0.5},
    'Fur Coat': {'category': 'Physical', 'multiplier': 0.5},
    'Marvel Scale': {'stat': 'defense', 'multiplier': 1.5, 'condition': 'has_status'},
    'Ice Scales': {'category': 'Special', 'multiplier': 0.5},
    'Fluffy': {'flag_reduce': 'contact', 'multiplier': 0.5, 'fire_weakness': 2.0},
}

# Abilities that grant type immunities (absorb/nullify certain types)
TYPE_IMMUNITY_ABILITIES = {
    'Levitate': {'immune_type': 'Ground'},
    'Flash Fire': {'immune_type': 'Fire', 'boost': 'fire_power'},
    'Water Absorb': {'immune_type': 'Water', 'heal': 0.25},
    'Volt Absorb': {'immune_type': 'Electric', 'heal': 0.25},
    'Lightning Rod': {'immune_type': 'Electric', 'boost_stat': 'sp_attack'},
    'Storm Drain': {'immune_type': 'Water', 'boost_stat': 'sp_attack'},
    'Motor Drive': {'immune_type': 'Electric', 'boost_stat': 'speed'},
    'Sap Sipper': {'immune_type': 'Grass', 'boost_stat': 'attack'},
    'Dry Skin': {'immune_type': 'Water', 'heal': 0.25},
    'Wonder Guard': {'only_super_effective': True},
    'Bulletproof': {'immune_flag': 'ball_bomb'},
    'Soundproof': {'immune_flag': 'sound'},
    'Overcoat': {'immune_flag': 'powder'},
}

# Abilities that prevent status conditions
STATUS_IMMUNITY_ABILITIES = {
    'Immunity': ['poison', 'badly_poison'],
    'Limber': ['paralysis'],
    'Insomnia': ['sleep'],
    'Vital Spirit': ['sleep'],
    'Water Veil': ['burn'],
    'Magma Armor': ['freeze'],
    'Own Tempo': ['confusion'],
    'Inner Focus': ['flinch'],
    'Oblivious': ['attract', 'taunt'],
    'Leaf Guard': {'conditions': ['burn', 'poison', 'badly_poison', 'paralysis', 'sleep', 'freeze'],
                   'weather': 'Sun'},
    'Sweet Veil': ['sleep'],  # Also protects allies in doubles
    'Comatose': ['burn', 'poison', 'badly_poison', 'paralysis', 'sleep', 'freeze'],
}

# Abilities that prevent stat drops
STAT_PROTECTION_ABILITIES = {
    'Clear Body': 'all',
    'White Smoke': 'all',
    'Full Metal Body': 'all',
    'Hyper Cutter': ['attack'],
    'Keen Eye': ['accuracy'],
    'Big Pecks': ['defense'],
}

# Abilities that trigger on contact (defender's ability activates when hit by contact move)
ON_CONTACT_ABILITIES = {
    'Static': {'status': 'paralysis', 'chance': 30},
    'Flame Body': {'status': 'burn', 'chance': 30},
    'Poison Point': {'status': 'poison', 'chance': 30},
    'Effect Spore': {'status': ['paralysis', 'poison', 'sleep'], 'chance': 30},  # 10% each
    'Cute Charm': {'status': 'attract', 'chance': 30},
    'Rough Skin': {'recoil': 1/8},
    'Iron Barbs': {'recoil': 1/8},
    'Mummy': {'replace_ability': 'Mummy'},
    'Gooey': {'stat': 'speed', 'change': -1},
    'Tangling Hair': {'stat': 'speed', 'change': -1},
    'Wandering Spirit': {'swap_ability': True},
}

# Abilities that trigger at end of turn
END_OF_TURN_ABILITIES = {
    'Speed Boost': {'stat': 'speed', 'change': 1},
    'Moody': {'random_boost': True},
    'Bad Dreams': {'damage_sleeping': 1/8},
    'Harvest': {'recover_berry': True},
    'Pickup': {'pickup_item': True},
}

# Abilities that modify speed
SPEED_MODIFIER_ABILITIES = {
    'Swift Swim': {'weather': 'Rain', 'multiplier': 2.0},
    'Chlorophyll': {'weather': 'Sun', 'multiplier': 2.0},
    'Sand Rush': {'weather': 'Sandstorm', 'multiplier': 2.0},
    'Slush Rush': {'weather': 'Hail', 'multiplier': 2.0},
    'Quick Feet': {'condition': 'has_status', 'multiplier': 1.5},
    'Unburden': {'condition': 'lost_item', 'multiplier': 2.0},
    'Stall': {'move_last': True},
    'Slow Start': {'turns': 5, 'multiplier': 0.5},
}

# Abilities that modify accuracy / evasion
ACCURACY_ABILITIES = {
    'Compound Eyes': {'accuracy_multiplier': 1.3},
    'Victory Star': {'accuracy_multiplier': 1.1},
    'Hustle': {'accuracy_multiplier': 0.8},  # Physical moves only
    'No Guard': {'always_hit': True, 'always_hit_by': True},
    'Sand Veil': {'evasion_boost': 1.25, 'weather': 'Sandstorm'},
    'Snow Cloak': {'evasion_boost': 1.25, 'weather': 'Hail'},
    'Tangled Feet': {'evasion_boost': 1.5, 'condition': 'confused'},
}

# Abilities that modify critical hit rates
CRIT_MODIFIER_ABILITIES = {
    'Super Luck': {'crit_stage_bonus': 1},
    'Battle Armor': {'block_crits': True},
    'Shell Armor': {'block_crits': True},
    'Merciless': {'auto_crit_condition': 'poison'},
}

# Abilities that trigger on stat changes
ON_STAT_CHANGE_ABILITIES = {
    'Defiant': {'on_stat_drop': {'stat': 'attack', 'change': 2}},
    'Competitive': {'on_stat_drop': {'stat': 'sp_attack', 'change': 2}},
    'Contrary': {'invert_stat_changes': True},
    'Simple': {'double_stat_changes': True},
}

# Abilities that trigger when the Pokemon KOs an opponent
ON_KO_ABILITIES = {
    'Moxie': {'stat': 'attack', 'change': 1},
    'Beast Boost': {'boost_highest_stat': True},
    'Soul-Heart': {'stat': 'sp_attack', 'change': 1},
    'Chilling Neigh': {'stat': 'attack', 'change': 1},
    'Grim Neigh': {'stat': 'sp_attack', 'change': 1},
}

# Abilities that trigger on taking a hit (attacker's ability)
ON_HIT_ATTACKER_ABILITIES = {
    'Stench': {'flinch_chance': 10},
    'Poison Touch': {'poison_chance': 30},
}

# Abilities that modify priority
PRIORITY_ABILITIES = {
    'Prankster': {'status_priority': 1},
    'Gale Wings': {'type_priority': {'type': 'Flying', 'priority': 1, 'condition': 'full_hp'}},
    'Triage': {'healing_priority': 3},
}

# Abilities that trigger on flinch/crit received
ON_FLINCH_ABILITIES = {
    'Steadfast': {'stat': 'speed', 'change': 1},
    'Inner Focus': {'prevent_flinch': True},
}

ON_CRIT_RECEIVED_ABILITIES = {
    'Anger Point': {'max_attack': True},
}

# Abilities that trigger on switch-out
SWITCH_OUT_ABILITIES = {
    'Natural Cure': {'cure_status': True},
    'Regenerator': {'heal': 1/3},
}

# Weather-related passive abilities (immunity/healing)
WEATHER_PASSIVE_ABILITIES = {
    'Rain Dish': {'weather': 'Rain', 'heal': 1/16},
    'Ice Body': {'weather': 'Hail', 'heal': 1/16, 'hail_immune': True},
    'Dry Skin': {'rain_heal': 1/8, 'sun_damage': 1/8},
    'Solar Power': {'sun_damage': 1/8},  # Also boosts SpAtk (in ATTACKER_DAMAGE)
    'Sand Veil': {'sandstorm_immune': True},
    'Sand Rush': {'sandstorm_immune': True},
    'Sand Force': {'sandstorm_immune': True},
    'Overcoat': {'weather_immune': True},
    'Magic Guard': {'indirect_damage_immune': True},
    'Snow Cloak': {'hail_immune': True},
}

# Abilities that prevent recoil
RECOIL_ABILITIES = {
    'Rock Head': {'prevent_recoil': True},
    'Magic Guard': {'prevent_indirect': True},
}

# Trapping abilities
TRAPPING_ABILITIES = {
    'Shadow Tag': {'trap_all': True, 'immune': ['Shadow Tag']},
    'Arena Trap': {'trap_grounded': True},
    'Magnet Pull': {'trap_type': 'Steel'},
}

# Abilities with unique/special mechanics
SPECIAL_ABILITIES = {
    'Protean': 'change_type_to_move',
    'Libero': 'change_type_to_move',
    'Color Change': 'change_type_to_hit',
    'Wonder Guard': 'only_super_effective',
    'Disguise': 'block_first_hit',
    'Sturdy': 'survive_ohko',
    'Magic Bounce': 'reflect_status',
    'Magic Guard': 'no_indirect_damage',
    'Mold Breaker': 'ignore_abilities',
    'Turboblaze': 'ignore_abilities',
    'Teravolt': 'ignore_abilities',
    'Unaware': 'ignore_stat_changes',
    'Parental Bond': 'hit_twice',
    'Skill Link': 'max_multi_hit',
    'Stance Change': 'aegislash_form',
    'Zen Mode': 'darmanitan_form',
    'Forecast': 'castform_form',
    'Illusion': 'disguise_as_last',
    'Imposter': 'transform_on_entry',
    'Schooling': 'wishiwashi_form',
    'Shields Down': 'minior_form',
    'Power Construct': 'zygarde_form',
    'Battle Bond': 'ash_greninja',
}

# Move flag sets for ability checks
PUNCH_MOVES = {
    'Bullet Punch', 'Comet Punch', 'Dizzy Punch', 'Drain Punch',
    'Dynamic Punch', 'Fire Punch', 'Focus Punch', 'Hammer Arm',
    'Ice Punch', 'Mach Punch', 'Mega Punch', 'Meteor Mash',
    'Power-Up Punch', 'Shadow Punch', 'Sky Uppercut', 'Thunder Punch',
    'Double Iron Bash', 'Plasma Fists'
}

BITE_MOVES = {
    'Bite', 'Crunch', 'Fire Fang', 'Ice Fang', 'Thunder Fang',
    'Poison Fang', 'Psychic Fangs', 'Hyper Fang', 'Jaw Lock',
    'Fishious Rend', 'Bolt Beak'
}

PULSE_MOVES = {
    'Aura Sphere', 'Dark Pulse', 'Dragon Pulse', 'Heal Pulse',
    'Origin Pulse', 'Water Pulse', 'Terrain Pulse'
}

SOUND_MOVES = {
    'Boomburst', 'Bug Buzz', 'Chatter', 'Clanging Scales',
    'Disarming Voice', 'Echoed Voice', 'Grasswhistle', 'Growl',
    'Heal Bell', 'Hyper Voice', 'Metal Sound', 'Noble Roar',
    'Overdrive', 'Parting Shot', 'Perish Song', 'Relic Song',
    'Roar', 'Round', 'Screech', 'Sing', 'Snarl', 'Snore',
    'Sparkling Aria', 'Supersonic', 'Uproar'
}

BALL_BOMB_MOVES = {
    'Acid Spray', 'Aura Sphere', 'Barrage', 'Bullet Seed',
    'Egg Bomb', 'Electro Ball', 'Energy Ball', 'Focus Blast',
    'Gyro Ball', 'Ice Ball', 'Magnet Bomb', 'Mist Ball',
    'Mud Bomb', 'Octazooka', 'Rock Wrecker', 'Seed Bomb',
    'Shadow Ball', 'Sludge Bomb', 'Weather Ball', 'Zap Cannon'
}

# Contact moves - most Physical moves make contact (simplified check)
# In a full implementation, this would be checked from the move database
CONTACT_OVERRIDE_NO = {
    'Earthquake', 'Bulldoze', 'Magnitude', 'Rock Slide', 'Rock Tomb',
    'Stone Edge', 'Stealth Rock', 'Bone Rush', 'Bonemerang',
    'Icicle Spear', 'Pin Missile', 'Spike Cannon', 'Rock Blast',
    'Bullet Seed', 'Seed Bomb', 'Razor Leaf', 'Petal Blizzard',
    'Thousand Arrows', 'Precipice Blades', 'Dragon Darts'
}


# =============================================================================
# ABILITY HANDLER CLASS
# =============================================================================

class AbilityHandler:
    """
    Central handler for all ability effects in battle.
    Methods are called from TurnManager at appropriate trigger points.
    """

    # *** PUBLIC STATIC ***
    # region Checks

    @staticmethod
    def check_burn_attack_reduction(attacker):
        """
        Check if burn's Attack reduction is negated by ability.
        
        Returns:
            bool: True if burn reduction should be ignored
        """
        ability = getattr(attacker, 'ability', None)
        return ability == 'Guts'

    @staticmethod
    def check_disguise(defender, move, log_func):
        """
        Check if Disguise activates (block first hit).
        
        Returns:
            bool: True if the hit was blocked
        """
        ability = getattr(defender, 'ability', None)
        if ability != 'Disguise':
            return False
        
        if not hasattr(defender, 'disguise_broken'):
            defender.disguise_broken = False
        
        if not defender.disguise_broken:
            defender.disguise_broken = True
            # Take 1/8 HP recoil in Gen 8+
            damage = max(1, defender.max_hp // 8)
            defender.take_damage(damage)
            log_func(f"{defender.name}'s Disguise was busted!")
            return True
        
        return False

    @staticmethod
    def check_indirect_damage_immunity(pokemon):
        """Check if Pokemon is immune to indirect damage (burn, poison, hazards, etc.)."""
        ability = getattr(pokemon, 'ability', None)
        return ability == 'Magic Guard'

    @staticmethod
    def check_magic_bounce(defender, move, log_func):
        """
        Check if Magic Bounce reflects a status move.
        
        Returns:
            bool: True if the move is reflected
        """
        ability = getattr(defender, 'ability', None)
        if ability != 'Magic Bounce':
            return False
        
        causes_damage = move.get('causes_damage', True) if isinstance(move, dict) else getattr(move, 'causes_damage', True)
        if not causes_damage:
            log_func(f"{defender.name}'s Magic Bounce reflected the move!")
            return True
        
        return False

    @staticmethod
    def check_mold_breaker(attacker):
        """Check if attacker has a Mold Breaker-type ability."""
        ability = getattr(attacker, 'ability', None)
        return ability in ('Mold Breaker', 'Turboblaze', 'Teravolt')

    @staticmethod
    def check_recoil_immunity(pokemon):
        """Check if Pokemon is immune to recoil damage."""
        ability = getattr(pokemon, 'ability', None)
        return ability in ('Rock Head', 'Magic Guard')

    @staticmethod
    def check_stat_drop_immunity(pokemon, stat_name, change, source_pokemon=None):
        """
        Check if the Pokemon's ability prevents stat drops.
        
        Returns:
            tuple: (is_blocked, counter_boost)
                - is_blocked (bool): True if the stat drop is blocked
                - counter_boost (tuple or None): (stat, amount) if counter-boost activates
        """
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return False, None
        
        if change >= 0:
            return False, None  # Only blocks drops
        
        # Contrary inverts stat changes
        if ability == 'Contrary':
            return False, None  # The inversion is handled in modify_stat_stage
        
        # Clear Body / White Smoke / Full Metal Body
        if ability in STAT_PROTECTION_ABILITIES:
            protection = STAT_PROTECTION_ABILITIES[ability]
            if protection == 'all':
                return True, None
            elif isinstance(protection, list) and stat_name in protection:
                return True, None
        
        # Defiant: Attack +2 when any stat is lowered
        if ability == 'Defiant':
            return False, ('attack', 2)
        
        # Competitive: Sp.Atk +2 when any stat is lowered
        if ability == 'Competitive':
            return False, ('sp_attack', 2)
        
        return False, None

    @staticmethod
    def check_status_immunity(pokemon, status, battle_state=None):
        """
        Check if the Pokemon's ability prevents a status condition.
        
        Returns:
            bool: True if the status is blocked
        """
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return False
        
        if ability in STATUS_IMMUNITY_ABILITIES:
            immunity = STATUS_IMMUNITY_ABILITIES[ability]
            if isinstance(immunity, list):
                return status in immunity
            elif isinstance(immunity, dict):
                # Conditional immunity (e.g., Leaf Guard)
                conditions = immunity.get('conditions', [])
                weather_req = immunity.get('weather')
                if weather_req and battle_state:
                    current_weather = battle_state.get('weather', {}).get('type')
                    if current_weather == weather_req:
                        return status in conditions
                    return False
                return status in conditions
        
        # Specific immunity combinations
        if ability == 'Comatose':
            return True  # Immune to all status (always considered asleep)
        
        return False

    @staticmethod
    def check_sturdy(pokemon, damage, log_func):
        """
        Check if Sturdy activates (survive OHKO at full HP).
        
        Returns:
            int: Modified damage (capped to leave 1 HP if Sturdy activates)
        """
        ability = getattr(pokemon, 'ability', None)
        if ability != 'Sturdy':
            return damage
        
        if pokemon.current_hp >= pokemon.max_hp and damage >= pokemon.current_hp:
            log_func(f"{pokemon.name} held on thanks to Sturdy!")
            return pokemon.current_hp - 1
        
        return damage

    @staticmethod
    def check_trapping(pokemon, opponent, battle_state, log_func):
        """
        Check if an ability traps the opponent.
        
        Returns:
            bool: True if the opponent is trapped
        """
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return False
        
        if ability == 'Shadow Tag':
            opp_ability = getattr(opponent, 'ability', None)
            if opp_ability != 'Shadow Tag':
                return True
        
        elif ability == 'Arena Trap':
            # Only trap grounded Pokemon
            if opponent.type1 != 'Flying' and opponent.type2 != 'Flying':
                opp_ability = getattr(opponent, 'ability', None)
                if opp_ability != 'Levitate':
                    return True
        
        elif ability == 'Magnet Pull':
            if opponent.type1 == 'Steel' or opponent.type2 == 'Steel':
                return True
        
        return False

    @staticmethod
    def check_type_change(attacker, move):
        """
        Check if ability changes the move's type (Pixilate, Refrigerate, etc.).
        
        Returns:
            tuple: (new_type, power_multiplier) or (None, 1.0) if no change
        """
        ability = getattr(attacker, 'ability', None)
        if not ability:
            return None, 1.0
        
        move_type = move.get('type', '') if isinstance(move, dict) else getattr(move, 'type', '')
        
        type_change_abilities = {
            'Normalize': ('Normal', 1.2),
            'Pixilate': ('Fairy', 1.2),
            'Refrigerate': ('Ice', 1.2),
            'Aerilate': ('Flying', 1.2),
            'Galvanize': ('Electric', 1.2),
        }
        
        if ability in type_change_abilities:
            new_type, mult = type_change_abilities[ability]
            if ability == 'Normalize':
                return new_type, mult
            elif move_type == 'Normal':
                return new_type, mult
        
        # Protean / Libero: change user's type to move's type
        if ability in ('Protean', 'Libero'):
            if move_type and move_type != 'Normal':
                attacker.type1 = move_type
                attacker.type2 = None
        
        return None, 1.0

    @staticmethod  
    def check_type_immunity(defender, move, battle_state, log_func):
        """
        Check if the defender's ability grants type immunity.
        Called BEFORE damage calculation.
        
        Returns:
            tuple: (is_immune, should_heal, stat_boost_info)
                - is_immune (bool): If True, move is completely blocked
                - should_heal (float): Fraction of max HP to heal (0 if no heal)
                - stat_boost (tuple or None): (stat_name, stages) if ability boosts a stat
        """
        ability = getattr(defender, 'ability', None)
        if not ability:
            return False, 0, None
        
        # Check for Mold Breaker
        # (caller should check attacker's ability before calling this)
        
        move_type = move.get('type', '') if isinstance(move, dict) else getattr(move, 'type', '')
        move_name = move.get('name', '') if isinstance(move, dict) else getattr(move, 'name', '')
        causes_damage = move.get('causes_damage', True) if isinstance(move, dict) else getattr(move, 'causes_damage', True)
        
        if not causes_damage:
            return False, 0, None
        
        # --- Levitate ---
        if ability == 'Levitate' and move_type == 'Ground':
            log_func(f"{defender.name}'s Levitate makes it immune to Ground moves!")
            return True, 0, None
        
        # --- Flash Fire ---
        elif ability == 'Flash Fire' and move_type == 'Fire':
            if not hasattr(defender, 'flash_fire_active'):
                defender.flash_fire_active = False
            defender.flash_fire_active = True
            log_func(f"{defender.name}'s Flash Fire powered up its Fire-type moves!")
            return True, 0, None
        
        # --- Water Absorb ---
        elif ability == 'Water Absorb' and move_type == 'Water':
            log_func(f"{defender.name}'s Water Absorb restored its HP!")
            return True, 0.25, None
        
        # --- Volt Absorb ---
        elif ability == 'Volt Absorb' and move_type == 'Electric':
            log_func(f"{defender.name}'s Volt Absorb restored its HP!")
            return True, 0.25, None
        
        # --- Dry Skin (water immunity + heal) ---
        elif ability == 'Dry Skin' and move_type == 'Water':
            log_func(f"{defender.name}'s Dry Skin restored its HP!")
            return True, 0.25, None
        
        # --- Lightning Rod ---
        elif ability == 'Lightning Rod' and move_type == 'Electric':
            log_func(f"{defender.name}'s Lightning Rod raised its Sp. Atk!")
            return True, 0, ('sp_attack', 1)
        
        # --- Storm Drain ---
        elif ability == 'Storm Drain' and move_type == 'Water':
            log_func(f"{defender.name}'s Storm Drain raised its Sp. Atk!")
            return True, 0, ('sp_attack', 1)
        
        # --- Motor Drive ---
        elif ability == 'Motor Drive' and move_type == 'Electric':
            log_func(f"{defender.name}'s Motor Drive raised its Speed!")
            return True, 0, ('speed', 1)
        
        # --- Sap Sipper ---
        elif ability == 'Sap Sipper' and move_type == 'Grass':
            log_func(f"{defender.name}'s Sap Sipper raised its Attack!")
            return True, 0, ('attack', 1)
        
        # --- Wonder Guard ---
        elif ability == 'Wonder Guard':
            # Check if move is super effective
            effectiveness = _calc_type_effectiveness(move_type, defender)
            if effectiveness <= 1.0:
                log_func(f"{defender.name}'s Wonder Guard blocked the attack!")
                return True, 0, None
        
        # --- Bulletproof ---
        elif ability == 'Bulletproof' and move_name in BALL_BOMB_MOVES:
            log_func(f"{defender.name}'s Bulletproof blocked {move_name}!")
            return True, 0, None
        
        # --- Soundproof ---
        elif ability == 'Soundproof' and move_name in SOUND_MOVES:
            log_func(f"{defender.name}'s Soundproof blocked {move_name}!")
            return True, 0, None
        
        # --- Overcoat (powder moves only) ---
        elif ability == 'Overcoat':
            powder_moves = {'Cotton Spore', 'Poison Powder', 'Powder', 'Rage Powder',
                           'Sleep Powder', 'Spore', 'Stun Spore'}
            if move_name in powder_moves:
                log_func(f"{defender.name}'s Overcoat blocks {move_name}!")
                return True, 0, None
        
        return False, 0, None

    @staticmethod
    def check_unaware(attacker, defender, move):
        """
        Check if Unaware applies (ignore stat changes).
        
        Returns:
            tuple: (ignore_attacker_boosts, ignore_defender_boosts)
        """
        attacker_ability = getattr(attacker, 'ability', None)
        defender_ability = getattr(defender, 'ability', None)
        
        ignore_attacker = defender_ability == 'Unaware'
        ignore_defender = attacker_ability == 'Unaware'
        
        return ignore_attacker, ignore_defender

    @staticmethod
    def check_weather_immunity(pokemon, weather_type):
        """
        Check if Pokemon is immune to weather damage.
        
        Returns:
            bool: True if immune
        """
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return False
        
        if ability == 'Magic Guard':
            return True  # Immune to all indirect damage
        elif ability == 'Overcoat':
            return True  # Immune to weather damage
        elif weather_type == 'Sandstorm':
            return ability in ('Sand Veil', 'Sand Rush', 'Sand Force')
        elif weather_type == 'Hail':
            return ability in ('Ice Body', 'Snow Cloak', 'Slush Rush')
        
        return False

    # endregion Checks

    @staticmethod
    def end_of_turn(pokemon, battle_state, log_func, opponents=None):
        """Handle abilities that activate at end of turn."""
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return
        
        weather = battle_state.get('weather', {}).get('type')
        
        # Bad Dreams
        if ability == 'Bad Dreams':
            if opponents:
                for opp in opponents:
                    if opp and opp.current_hp > 0 and opp.status == 'sleep':
                        damage = max(1, opp.max_hp // 8)
                        opp.take_damage(damage)
                        log_func(f"{opp.name} was tormented by {pokemon.name}'s Bad Dreams! (-{damage} HP)")
        
        # Rain Dish
        elif ability == 'Rain Dish' and weather == 'Rain':
            heal = max(1, pokemon.max_hp // 16)
            pokemon.heal(heal)
            log_func(f"{pokemon.name} restored HP with Rain Dish!")
        
        # Ice Body
        elif ability == 'Ice Body' and weather == 'Hail':
            heal = max(1, pokemon.max_hp // 16)
            pokemon.heal(heal)
            log_func(f"{pokemon.name} restored HP with Ice Body!")
        
        # Dry Skin (weather effects)
        elif ability == 'Dry Skin':
            if weather == 'Rain':
                heal = max(1, pokemon.max_hp // 8)
                pokemon.heal(heal)
                log_func(f"{pokemon.name} restored HP with Dry Skin!")
            elif weather == 'Sun':
                damage = max(1, pokemon.max_hp // 8)
                pokemon.take_damage(damage)
                log_func(f"{pokemon.name} was hurt by the sunlight! (-{damage} HP)")
        
        # Solar Power (sun damage)
        elif ability == 'Solar Power' and weather == 'Sun':
            damage = max(1, pokemon.max_hp // 8)
            pokemon.take_damage(damage)
            log_func(f"{pokemon.name} was hurt by Solar Power! (-{damage} HP)")
        
        # Speed Boost (moved to start_of_turn but some games do end of turn)
        # Already handled in start_of_turn
        
        # Moody
        elif ability == 'Moody':
            stats = ['attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
            boost_stat = random.choice(stats)
            remaining = [s for s in stats if s != boost_stat]
            drop_stat = random.choice(remaining)
            pokemon.modify_stat_stage(boost_stat, 2)
            pokemon.modify_stat_stage(drop_stat, -1)
            boost_display = boost_stat.replace('_', ' ').title()
            drop_display = drop_stat.replace('_', ' ').title()
            log_func(f"{pokemon.name}'s Moody sharply raised its {boost_display} and lowered its {drop_display}!")

    @staticmethod
    def get_flash_fire_boost(attacker):
        """Check if Flash Fire boost is active (1.5x to Fire moves)."""
        ability = getattr(attacker, 'ability', None)
        if ability == 'Flash Fire' and getattr(attacker, 'flash_fire_active', False):
            return 1.5
        return 1.0
    # region Modifiers

    @staticmethod
    def modify_accuracy(attacker, defender, move_accuracy, move, battle_state):
        """
        Modify accuracy based on abilities.
        
        Returns:
            tuple: (modified_accuracy, always_hit)
        """
        attacker_ability = getattr(attacker, 'ability', None)
        defender_ability = getattr(defender, 'ability', None)
        
        accuracy = move_accuracy
        
        # Attacker abilities
        if attacker_ability == 'Compound Eyes':
            accuracy = int(accuracy * 1.3)
        elif attacker_ability == 'Victory Star':
            accuracy = int(accuracy * 1.1)
        elif attacker_ability == 'Hustle':
            category = move.get('category', 'Physical') if isinstance(move, dict) else getattr(move, 'category', 'Physical')
            if category == 'Physical':
                accuracy = int(accuracy * 0.8)
        elif attacker_ability == 'No Guard':
            return accuracy, True  # Always hits
        
        # Defender abilities
        if defender_ability == 'No Guard':
            return accuracy, True  # Always gets hit too
        
        weather = battle_state.get('weather', {}).get('type')
        if defender_ability == 'Sand Veil' and weather == 'Sandstorm':
            accuracy = int(accuracy * 0.8)
        elif defender_ability == 'Snow Cloak' and weather == 'Hail':
            accuracy = int(accuracy * 0.8)
        elif defender_ability == 'Tangled Feet' and getattr(defender, 'confused', False):
            accuracy = int(accuracy * 0.5)
        
        return accuracy, False

    @staticmethod
    def modify_crit_damage(attacker, crit_multiplier):
        """Modify crit damage multiplier (e.g., Sniper)."""
        ability = getattr(attacker, 'ability', None)
        if ability == 'Sniper':
            return 2.25
        return crit_multiplier

    @staticmethod
    def modify_crit_stage(attacker, defender, crit_stage):
        """
        Modify critical hit stage based on abilities.
        
        Returns:
            tuple: (modified_crit_stage, crit_blocked)
        """
        attacker_ability = getattr(attacker, 'ability', None)
        defender_ability = getattr(defender, 'ability', None)
        
        stage = crit_stage
        
        # Attacker crit boost
        if attacker_ability == 'Super Luck':
            stage += 1
        elif attacker_ability == 'Merciless':
            if defender.status in ('poison', 'badly_poison'):
                stage = 3  # Guaranteed crit
        
        # Defender crit block
        if defender_ability in ('Battle Armor', 'Shell Armor'):
            return stage, True
        
        return stage, False

    @staticmethod
    def modify_incoming_damage(attacker, defender, move, damage, effectiveness, 
                                battle_state, is_contact=False):
        """
        Modify damage received by the defender based on abilities.
        Called during damage calculation.
        
        Returns:
            float: Damage multiplier to apply
        """
        ability = getattr(defender, 'ability', None)
        if not ability:
            return 1.0
        
        # Check if attacker has Mold Breaker
        attacker_ability = getattr(attacker, 'ability', None)
        if attacker_ability in ('Mold Breaker', 'Turboblaze', 'Teravolt'):
            # Mold Breaker ignores most defensive abilities
            if ability not in ('Full Metal Body', 'Prism Armor', 'Shadow Shield'):
                return 1.0
        
        move_type = move.get('type', '') if isinstance(move, dict) else getattr(move, 'type', '')
        category = move.get('category', 'Physical') if isinstance(move, dict) else getattr(move, 'category', 'Physical')
        
        multiplier = 1.0
        
        # --- Type resistance ---
        if ability == 'Thick Fat':
            if move_type in ('Fire', 'Ice'):
                multiplier *= 0.5
        
        elif ability == 'Heatproof':
            if move_type == 'Fire':
                multiplier *= 0.5
        
        elif ability == 'Dry Skin':
            if move_type == 'Fire':
                multiplier *= 1.25  # Takes MORE fire damage
        
        # --- Super effective resistance ---
        elif ability in ('Filter', 'Solid Rock', 'Prism Armor'):
            if effectiveness > 1.0:
                multiplier *= 0.75
        
        # --- Full HP bonus ---
        elif ability in ('Multiscale', 'Shadow Shield'):
            if defender.current_hp >= defender.max_hp:
                multiplier *= 0.5
        
        # --- Category resistance ---
        elif ability == 'Fur Coat':
            if category == 'Physical':
                multiplier *= 0.5
        
        elif ability == 'Ice Scales':
            if category == 'Special':
                multiplier *= 0.5
        
        elif ability == 'Marvel Scale':
            if defender.status and defender.status != 'healthy':
                if category == 'Physical':
                    multiplier *= 0.67  # ~1.5x defense
        
        elif ability == 'Fluffy':
            if is_contact:
                multiplier *= 0.5
            if move_type == 'Fire':
                multiplier *= 2.0
        
        return multiplier

    @staticmethod
    def modify_multi_hit(attacker, num_hits):
        """Modify multi-hit count (Skill Link always gets max hits)."""
        ability = getattr(attacker, 'ability', None)
        if ability == 'Skill Link':
            return 5
        elif ability == 'Parental Bond':
            return 2  # Hits twice (second hit at reduced power)
        return num_hits

    @staticmethod
    def modify_outgoing_damage(attacker, defender, move, base_power, damage, 
                                effectiveness, battle_state, is_contact=False):
        """
        Modify damage dealt by the attacker based on abilities.
        Called during damage calculation.
        
        Returns:
            tuple: (modified_power, power_multiplier, extra_multiplier)
        """
        ability = getattr(attacker, 'ability', None)
        if not ability:
            return base_power, 1.0, 1.0
        
        power = base_power
        multiplier = 1.0
        move_type = move.get('type', '') if isinstance(move, dict) else getattr(move, 'type', '')
        move_name = move.get('name', '') if isinstance(move, dict) else getattr(move, 'name', '')
        category = move.get('category', 'Physical') if isinstance(move, dict) else getattr(move, 'category', 'Physical')
        
        # --- Raw stat multipliers ---
        if ability == 'Huge Power' or ability == 'Pure Power':
            if category == 'Physical':
                multiplier *= 2.0
        
        elif ability == 'Hustle':
            if category == 'Physical':
                multiplier *= 1.5
        
        # --- Conditional boosts ---
        elif ability == 'Guts':
            if attacker.status and attacker.status != 'healthy':
                if category == 'Physical':
                    multiplier *= 1.5
        
        elif ability == 'Toxic Boost':
            if attacker.status in ('poison', 'badly_poison'):
                if category == 'Physical':
                    multiplier *= 1.5
        
        elif ability == 'Flare Boost':
            if attacker.status == 'burn':
                if category == 'Special':
                    multiplier *= 1.5
        
        elif ability == 'Defeatist':
            if attacker.current_hp <= attacker.max_hp // 2:
                multiplier *= 0.5
        
        # --- Type-based boosts at low HP ---
        elif ability in ('Blaze', 'Torrent', 'Overgrow', 'Swarm'):
            type_map = {'Blaze': 'Fire', 'Torrent': 'Water', 'Overgrow': 'Grass', 'Swarm': 'Bug'}
            if move_type == type_map.get(ability) and attacker.current_hp <= attacker.max_hp // 3:
                multiplier *= 1.5
        
        # --- Weather-based boosts ---
        elif ability == 'Solar Power':
            weather = battle_state.get('weather', {}).get('type')
            if weather == 'Sun' and category == 'Special':
                multiplier *= 1.5
        
        elif ability == 'Sand Force':
            weather = battle_state.get('weather', {}).get('type')
            if weather == 'Sandstorm' and move_type in ('Rock', 'Ground', 'Steel'):
                multiplier *= 1.3
        
        # --- Move category boosts ---
        elif ability == 'Technician':
            if power and power <= 60:
                multiplier *= 1.5
        
        elif ability == 'Iron Fist':
            if move_name in PUNCH_MOVES:
                multiplier *= 1.2
        
        elif ability == 'Strong Jaw':
            if move_name in BITE_MOVES:
                multiplier *= 1.5
        
        elif ability == 'Mega Launcher':
            if move_name in PULSE_MOVES:
                multiplier *= 1.5
        
        elif ability == 'Reckless':
            # Boost recoil moves
            effects = move.get('effects', []) if isinstance(move, dict) else getattr(move, 'effects', [])
            has_recoil = any(e.get('effect_type') == 'RECOIL' for e in (effects or []))
            if has_recoil:
                multiplier *= 1.2
        
        elif ability == 'Tough Claws':
            if is_contact:
                multiplier *= 1.3
        
        elif ability == 'Sharpness':
            slicing_moves = {'Air Cutter', 'Air Slash', 'Aerial Ace', 'Cross Poison',
                           'Cut', 'Fury Cutter', 'Leaf Blade', 'Night Slash',
                           'Psycho Cut', 'Razor Leaf', 'Razor Shell', 'Sacred Sword',
                           'Slash', 'Solar Blade', 'X-Scissor'}
            if move_name in slicing_moves:
                multiplier *= 1.5
        
        elif ability == 'Sheer Force':
            effects = move.get('effects', []) if isinstance(move, dict) else getattr(move, 'effects', [])
            has_secondary = any(
                e.get('probability', 100) < 100 
                for e in (effects or [])
                if e.get('effect_type') in ('STATUS', 'STAT_CHANGE', 'OTHER')
            )
            if has_secondary:
                multiplier *= 1.3
        
        elif ability == 'Analytic':
            # Simplified: check if attacker moved last (approximation)
            # In full implementation, would track move order
            pass
        
        elif ability == 'Flower Gift':
            weather = battle_state.get('weather', {}).get('type')
            if weather == 'Sun' and category == 'Physical':
                multiplier *= 1.5
        
        return power, multiplier, 1.0

    @staticmethod
    def modify_speed(pokemon, base_speed, battle_state):
        """
        Modify speed based on ability.
        
        Returns:
            int: Modified speed value
        """
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return base_speed
        
        weather = battle_state.get('weather', {}).get('type')
        speed = base_speed
        
        if ability == 'Swift Swim' and weather == 'Rain':
            speed *= 2
        elif ability == 'Chlorophyll' and weather == 'Sun':
            speed *= 2
        elif ability == 'Sand Rush' and weather == 'Sandstorm':
            speed *= 2
        elif ability == 'Slush Rush' and weather == 'Hail':
            speed *= 2
        elif ability == 'Quick Feet' and pokemon.status and pokemon.status != 'healthy':
            speed = int(speed * 1.5)
        elif ability == 'Unburden':
            if hasattr(pokemon, 'lost_item') and pokemon.lost_item:
                speed *= 2
        elif ability == 'Slow Start':
            turns = getattr(pokemon, 'turns_active', 0)
            if turns < 5:
                speed //= 2
        
        return int(speed)

    @staticmethod
    def modify_stab(attacker, base_stab):
        """
        Modify STAB multiplier (Adaptability makes it 2.0 instead of 1.5).
        
        Returns:
            float: Modified STAB multiplier
        """
        ability = getattr(attacker, 'ability', None)
        if ability == 'Adaptability':
            return 2.0
        return base_stab

    @staticmethod
    def modify_stat_change(pokemon, stat, change):
        """
        Modify stat changes based on ability (Contrary, Simple).
        
        Returns:
            int: Modified change amount
        """
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return change
        
        if ability == 'Contrary':
            return -change
        elif ability == 'Simple':
            return change * 2
        
        return change

    # endregion Modifiers
    # region Event handlers

    @staticmethod
    def on_after_attacking(attacker, defender, move, damage_dealt, log_func, battle_state=None):
        """
        Handle attacker's ability triggering after hitting the target.
        """
        ability = getattr(attacker, 'ability', None)
        if not ability:
            return
        
        move_name = move.get('name', '') if isinstance(move, dict) else getattr(move, 'name', '')
        
        if ability == 'Stench':
            if random.random() < 0.10:
                if not hasattr(defender, 'flinched'):
                    defender.flinched = False
                defender.flinched = True
        
        elif ability == 'Poison Touch':
            category = move.get('category', 'Physical') if isinstance(move, dict) else getattr(move, 'category', 'Physical')
            is_contact = category == 'Physical' and move_name not in CONTACT_OVERRIDE_NO
            if is_contact and random.random() < 0.30 and not defender.status:
                defender.apply_status('poison')
                log_func(f"{attacker.name}'s Poison Touch poisoned {defender.name}!")

    @staticmethod
    def on_before_move(attacker, move, battle_state, log_func):
        """
        Handle abilities that trigger just before using a move.
        (Protean type change, etc.)
        """
        ability = getattr(attacker, 'ability', None)
        if not ability:
            return
        
        move_type = move.get('type', '') if isinstance(move, dict) else getattr(move, 'type', '')
        
        if ability in ('Protean', 'Libero'):
            if move_type and (move_type != attacker.type1 or attacker.type2 is not None):
                attacker.type1 = move_type
                attacker.type2 = None
                log_func(f"{attacker.name}'s {ability} changed its type to {move_type}!")

    @staticmethod
    def on_contact(attacker, defender, move, log_func, battle_state=None):
        """
        Handle defender's ability triggering on being hit by a contact move.
        
        Args:
            attacker: The Pokemon making contact
            defender: The Pokemon being hit
            move: The move used
            log_func: Logging function
        """
        ability = getattr(defender, 'ability', None)
        if not ability:
            return
        
        # Check if move makes contact
        move_name = move.get('name', '') if isinstance(move, dict) else getattr(move, 'name', '')
        category = move.get('category', 'Physical') if isinstance(move, dict) else getattr(move, 'category', 'Physical')
        
        is_contact = category == 'Physical' and move_name not in CONTACT_OVERRIDE_NO
        if not is_contact:
            return
        
        if ability == 'Static':
            if random.random() < 0.30 and not attacker.status:
                attacker.apply_status('paralysis')
                log_func(f"{defender.name}'s Static paralyzed {attacker.name}!")
        
        elif ability == 'Flame Body':
            if random.random() < 0.30 and not attacker.status:
                attacker.apply_status('burn')
                log_func(f"{defender.name}'s Flame Body burned {attacker.name}!")
        
        elif ability == 'Poison Point':
            if random.random() < 0.30 and not attacker.status:
                attacker.apply_status('poison')
                log_func(f"{defender.name}'s Poison Point poisoned {attacker.name}!")
        
        elif ability == 'Effect Spore':
            if random.random() < 0.30 and not attacker.status:
                roll = random.random()
                if roll < 0.33:
                    attacker.apply_status('paralysis')
                    log_func(f"{defender.name}'s Effect Spore paralyzed {attacker.name}!")
                elif roll < 0.66:
                    attacker.apply_status('poison')
                    log_func(f"{defender.name}'s Effect Spore poisoned {attacker.name}!")
                else:
                    attacker.apply_status('sleep', random.randint(1, 3))
                    log_func(f"{defender.name}'s Effect Spore put {attacker.name} to sleep!")
        
        elif ability == 'Cute Charm':
            if random.random() < 0.30:
                if not hasattr(attacker, 'attracted'):
                    attacker.attracted = False
                attacker.attracted = True
                log_func(f"{defender.name}'s Cute Charm infatuated {attacker.name}!")
        
        elif ability in ('Rough Skin', 'Iron Barbs'):
            recoil = max(1, defender.max_hp // 8)
            attacker.take_damage(recoil)
            log_func(f"{attacker.name} was hurt by {defender.name}'s {ability}! (-{recoil} HP)")
        
        elif ability == 'Mummy':
            old_ability = getattr(attacker, 'ability', None)
            if old_ability and old_ability not in ('Multitype', 'Stance Change', 'Schooling',
                                                    'Comatose', 'Shields Down', 'Disguise',
                                                    'RKS System', 'Battle Bond', 'Power Construct',
                                                    'Mummy'):
                attacker.ability = 'Mummy'
                log_func(f"{attacker.name}'s ability became Mummy!")
        
        elif ability in ('Gooey', 'Tangling Hair'):
            attacker.modify_stat_stage('speed', -1)
            log_func(f"{defender.name}'s {ability} lowered {attacker.name}'s Speed!")

    @staticmethod
    def on_crit_received(defender, log_func):
        """Handle abilities that trigger when receiving a critical hit."""
        ability = getattr(defender, 'ability', None)
        if not ability:
            return
        
        if ability == 'Anger Point':
            defender.stat_stages['attack'] = 6
            log_func(f"{defender.name}'s Anger Point maxed its Attack!")

    @staticmethod
    def on_flinch(pokemon, log_func):
        """Handle abilities that trigger when the Pokemon flinches."""
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return False  # Not prevented
        
        if ability == 'Inner Focus':
            log_func(f"{pokemon.name}'s Inner Focus prevented flinching!")
            return True  # Flinch prevented
        
        if ability == 'Steadfast':
            pokemon.modify_stat_stage('speed', 1)
            log_func(f"{pokemon.name}'s Steadfast raised its Speed!")
            return False  # Still flinches
        
        return False

    @staticmethod
    def on_ko(attacker, log_func):
        """Handle abilities that trigger when the attacker KOs a target."""
        ability = getattr(attacker, 'ability', None)
        if not ability:
            return
        
        if ability == 'Moxie':
            attacker.modify_stat_stage('attack', 1)
            log_func(f"{attacker.name}'s Moxie raised its Attack!")
        
        elif ability == 'Beast Boost':
            # Boost highest stat
            stats = {
                'attack': attacker.attack,
                'defense': attacker.defense,
                'sp_attack': attacker.sp_attack,
                'sp_defense': attacker.sp_defense,
                'speed': attacker.speed
            }
            best_stat = max(stats, key=stats.get)
            attacker.modify_stat_stage(best_stat, 1)
            stat_display = best_stat.replace('_', ' ').title()
            log_func(f"{attacker.name}'s Beast Boost raised its {stat_display}!")
        
        elif ability == 'Soul-Heart':
            attacker.modify_stat_stage('sp_attack', 1)
            log_func(f"{attacker.name}'s Soul-Heart raised its Sp. Atk!")

    @staticmethod
    def on_switch_in(pokemon, battle_state, log_func, opponents=None):
        """
        Handle abilities that activate when a Pokemon switches in.
        
        Args:
            pokemon: The Pokemon switching in
            battle_state: Current battle state dict
            log_func: Function to log messages
            opponents: List of opponent Pokemon
        """
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return
        
        # --- Weather setters ---
        if ability == 'Drought':
            battle_state['weather'] = {'type': 'Sun', 'turns_remaining': 5}
            log_func(f"{pokemon.name}'s Drought intensified the sun!")
        elif ability == 'Drizzle':
            battle_state['weather'] = {'type': 'Rain', 'turns_remaining': 5}
            log_func(f"{pokemon.name}'s Drizzle made it rain!")
        elif ability == 'Sand Stream':
            battle_state['weather'] = {'type': 'Sandstorm', 'turns_remaining': 5}
            log_func(f"{pokemon.name}'s Sand Stream whipped up a sandstorm!")
        elif ability == 'Snow Warning':
            battle_state['weather'] = {'type': 'Hail', 'turns_remaining': 5}
            log_func(f"{pokemon.name}'s Snow Warning made it hail!")
        elif ability == 'Desolate Land':
            battle_state['weather'] = {'type': 'Sun', 'turns_remaining': 999}
            log_func(f"{pokemon.name}'s Desolate Land created extremely harsh sunlight!")
        elif ability == 'Primordial Sea':
            battle_state['weather'] = {'type': 'Rain', 'turns_remaining': 999}
            log_func(f"{pokemon.name}'s Primordial Sea created heavy rain!")
        elif ability == 'Delta Stream':
            battle_state['weather'] = {'type': 'Strong Wind', 'turns_remaining': 999}
            log_func(f"{pokemon.name}'s Delta Stream created mysterious air currents!")
        
        # --- Terrain setters ---
        elif ability == 'Electric Surge':
            _set_terrain(battle_state, 'Electric', log_func, pokemon)
        elif ability == 'Grassy Surge':
            _set_terrain(battle_state, 'Grassy', log_func, pokemon)
        elif ability == 'Misty Surge':
            _set_terrain(battle_state, 'Misty', log_func, pokemon)
        elif ability == 'Psychic Surge':
            _set_terrain(battle_state, 'Psychic', log_func, pokemon)
        
        # --- Intimidate ---
        elif ability == 'Intimidate':
            if opponents:
                for opp in opponents:
                    if opp and opp.current_hp > 0:
                        # Check for Intimidate immunity
                        opp_ability = getattr(opp, 'ability', None)
                        if opp_ability in ('Clear Body', 'White Smoke', 'Full Metal Body',
                                           'Hyper Cutter', 'Inner Focus', 'Own Tempo',
                                           'Oblivious', 'Scrappy'):
                            log_func(f"{opp.name}'s {opp_ability} prevents Intimidate!")
                        elif opp_ability == 'Defiant':
                            opp.modify_stat_stage('attack', -1)
                            log_func(f"{pokemon.name}'s Intimidate lowered {opp.name}'s Attack!")
                            opp.modify_stat_stage('attack', 2)
                            log_func(f"{opp.name}'s Defiant sharply raised its Attack!")
                        elif opp_ability == 'Competitive':
                            opp.modify_stat_stage('attack', -1)
                            log_func(f"{pokemon.name}'s Intimidate lowered {opp.name}'s Attack!")
                            opp.modify_stat_stage('sp_attack', 2)
                            log_func(f"{opp.name}'s Competitive sharply raised its Sp. Atk!")
                        elif opp_ability == 'Contrary':
                            opp.modify_stat_stage('attack', 1)
                            log_func(f"{pokemon.name}'s Intimidate raised {opp.name}'s Attack! (Contrary)")
                        else:
                            opp.modify_stat_stage('attack', -1)
                            log_func(f"{pokemon.name}'s Intimidate lowered {opp.name}'s Attack!")
        
        # --- Download ---
        elif ability == 'Download':
            if opponents:
                opp = opponents[0]
                if opp and opp.current_hp > 0:
                    if opp.get_effective_stat('defense') < opp.get_effective_stat('sp_defense'):
                        pokemon.modify_stat_stage('attack', 1)
                        log_func(f"{pokemon.name}'s Download raised its Attack!")
                    else:
                        pokemon.modify_stat_stage('sp_attack', 1)
                        log_func(f"{pokemon.name}'s Download raised its Sp. Atk!")
        
        # --- Trace ---
        elif ability == 'Trace':
            if opponents:
                opp = opponents[0]
                opp_ability = getattr(opp, 'ability', None)
                if opp_ability and opp_ability not in ('Trace', 'Multitype', 'Illusion',
                                                       'Flower Gift', 'Imposter', 'Stance Change',
                                                       'Power of Alchemy', 'Receiver', 'Schooling',
                                                       'Disguise', 'Battle Bond', 'Power Construct',
                                                       'Shields Down', 'Comatose', 'RKS System'):
                    pokemon.ability = opp_ability
                    log_func(f"{pokemon.name} traced {opp.name}'s {opp_ability}!")
        
        # --- Imposter (Transform) ---
        elif ability == 'Imposter':
            if opponents:
                opp = opponents[0]
                if opp and opp.current_hp > 0 and hasattr(pokemon, 'transform'):
                    pokemon.transform(opp)
                    log_func(f"{pokemon.name} transformed into {opp.name}!")
        
        # --- Pressure ---
        elif ability == 'Pressure':
            log_func(f"{pokemon.name} is exerting its Pressure!")
        
        # --- Mold Breaker, Turboblaze, Teravolt ---
        elif ability in ('Mold Breaker', 'Turboblaze', 'Teravolt'):
            log_func(f"{pokemon.name} breaks the mold!")
        
        # --- Unnerve ---
        elif ability == 'Unnerve':
            log_func(f"{pokemon.name}'s Unnerve makes the opposing team too nervous to eat Berries!")
        
        # --- Air Lock / Cloud Nine ---
        elif ability in ('Air Lock', 'Cloud Nine'):
            log_func(f"{pokemon.name}'s {ability} negates the effects of weather!")
        
        # --- Frisk ---
        elif ability == 'Frisk':
            if opponents:
                for opp in opponents:
                    item = getattr(opp, 'held_item', None)
                    if item:
                        log_func(f"{pokemon.name} frisked {opp.name} and found its {item}!")
        
        # --- Anticipation ---
        elif ability == 'Anticipation':
            log_func(f"{pokemon.name} shuddered!")
        
        # --- Forewarn ---
        elif ability == 'Forewarn':
            if opponents:
                opp = opponents[0]
                if opp and hasattr(opp, 'moves') and opp.moves:
                    strongest = max(opp.moves, key=lambda m: m.get('power', 0) if isinstance(m, dict) else getattr(m, 'power', 0) or 0)
                    move_name = strongest.get('name', '???') if isinstance(strongest, dict) else getattr(strongest, 'name', '???')
                    log_func(f"{pokemon.name}'s Forewarn alerted it to {move_name}!")

    @staticmethod
    def on_switch_out(pokemon, log_func):
        """Handle abilities that trigger on switch-out."""
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return
        
        if ability == 'Natural Cure':
            if pokemon.status and pokemon.status != 'healthy':
                pokemon.cure_status()
                log_func(f"{pokemon.name}'s Natural Cure cured its status condition!")
        
        elif ability == 'Regenerator':
            heal = pokemon.max_hp // 3
            pokemon.heal(heal)
            log_func(f"{pokemon.name}'s Regenerator restored its HP!")

    # endregion Event handlers

    @staticmethod
    def start_of_turn(pokemon, battle_state, log_func):
        """Handle abilities that activate at the start of each turn."""
        ability = getattr(pokemon, 'ability', None)
        if not ability:
            return
        
        # Speed Boost
        if ability == 'Speed Boost':
            # Only boost if the Pokemon has been out for at least 1 turn
            turns = getattr(pokemon, 'turns_active', 0)
            if turns > 0:
                pokemon.modify_stat_stage('speed', 1)
                log_func(f"{pokemon.name}'s Speed Boost raised its Speed!")
        
        # Shed Skin
        elif ability == 'Shed Skin':
            if pokemon.status and pokemon.status != 'healthy':
                if random.random() < 0.33:
                    old_status = pokemon.status
                    pokemon.cure_status()
                    log_func(f"{pokemon.name}'s Shed Skin cured its {old_status}!")
        
        # Poison Heal
        elif ability == 'Poison Heal':
            if pokemon.status in ('poison', 'badly_poison'):
                heal = pokemon.max_hp // 8
                pokemon.heal(heal)
                log_func(f"{pokemon.name} restored HP with Poison Heal!")
        
        # Hydration
        elif ability == 'Hydration':
            weather = battle_state.get('weather', {}).get('type')
            if weather == 'Rain' and pokemon.status and pokemon.status != 'healthy':
                old_status = pokemon.status
                pokemon.cure_status()
                log_func(f"{pokemon.name}'s Hydration cured its {old_status}!")
        
        # Slow Start
        elif ability == 'Slow Start':
            turns = getattr(pokemon, 'turns_active', 0)
            if turns == 5:
                log_func(f"{pokemon.name} finally got its act together!")


def _calc_type_effectiveness(attack_type, defender):
    """Simple type effectiveness check for Wonder Guard."""
    return _const_type_eff(attack_type, defender.type1, getattr(defender, 'type2', None))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _set_terrain(battle_state, terrain_type, log_func, pokemon):
    """Set terrain on the battlefield."""
    if 'field_effects' not in battle_state:
        battle_state['field_effects'] = {}
    battle_state['field_effects']['terrain'] = {
        'type': terrain_type,
        'turns_remaining': 5
    }
    log_func(f"{pokemon.name}'s {terrain_type} Surge set {terrain_type} Terrain!")
