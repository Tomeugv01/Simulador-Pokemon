import sqlite3
import os
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path="data/pokemon_battle.db"):
        self.db_path = db_path
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def initialize_database(self):
        """Create all tables and insert initial data"""
        # Remove existing database file to start fresh
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print("Removed existing database file")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create tables in the correct order
        self._create_tables(cursor)
        
        # Insert data in the correct order
        print("Inserting types...")
        self._insert_types(cursor)
        
        print("Inserting move effects...")
        self._insert_move_effects(cursor)
        
        # Verify Force Berry was inserted
        cursor.execute("SELECT id, name FROM move_effects WHERE name = 'Force Berry'")
        force_berry = cursor.fetchone()
        if force_berry:
            print(f"✓ Force Berry inserted successfully with ID: {force_berry[0]}")
        else:
            print("✗ Force Berry NOT found in database!")
            return
        
        # Insert moves
        print("Inserting moves...")
        self._insert_moves(cursor)
        
        # Link moves to effects
        print("Linking moves to effects...")
        self._insert_move_effect_instances(cursor)
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")

    def _create_tables(self, cursor):
        """Create all tables"""
        # Create types table
        cursor.execute('''
        CREATE TABLE types (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
        ''')
        
        # Create move_effects table
        cursor.execute('''
        CREATE TABLE move_effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            effect_type TEXT NOT NULL CHECK(effect_type IN ('STATUS', 'STAT_CHANGE', 'HEAL', 'DAMAGE_MODIFIER', 'FIELD_EFFECT', 'WEATHER', 'RECOIL', 'OTHER')),
            status_condition TEXT CHECK(status_condition IN ('Burn', 'Paralysis', 'Freeze', 'Poison', 'Sleep', 'Confusion', 'None')) DEFAULT 'None',
            stat_to_change TEXT CHECK(stat_to_change IN ('Attack', 'Defense', 'SpAttack', 'SpDefense', 'Speed', 'Accuracy', 'Evasion', 'All')) DEFAULT NULL,
            stat_change_amount INTEGER DEFAULT 0,
            heal_percentage INTEGER DEFAULT 0,
            heal_fixed_amount INTEGER DEFAULT 0,
            recoil_percentage INTEGER DEFAULT 0,
            weather_type TEXT CHECK(weather_type IN ('Sun', 'Rain', 'Sandstorm', 'Hail', 'None')) DEFAULT 'None',
            field_condition TEXT DEFAULT NULL,
            effect_target TEXT CHECK(effect_target IN ('User', 'Target', 'AllPokemon', 'UserSide', 'TargetSide', 'Field')) DEFAULT 'Target',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create moves table
        cursor.execute('''
        CREATE TABLE moves (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('Physical', 'Special', 'Status')),
            pp INTEGER NOT NULL,
            power INTEGER,
            accuracy INTEGER,
            causes_damage BOOLEAN NOT NULL DEFAULT FALSE,
            makes_contact BOOLEAN DEFAULT FALSE,
            priority INTEGER DEFAULT 0,
            target_type TEXT CHECK(target_type IN ('Normal', 'Self', 'Adjacent_Ally', 'All_Adjacent', 'All_Adjacent_Foes', 'All', 'Field', 'Opponents_Field', 'UserSide')) DEFAULT 'Normal',
            description TEXT
        )
        ''')
        
        # Create move_effect_instances table
        cursor.execute('''
        CREATE TABLE move_effect_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id INTEGER NOT NULL,
            effect_id INTEGER NOT NULL,
            probability INTEGER NOT NULL DEFAULT 100,
            effect_order INTEGER NOT NULL DEFAULT 1,
            triggers_on TEXT CHECK(triggers_on IN ('Always', 'OnHit', 'OnCrit', 'IfSecondary', 'IfMiss')) DEFAULT 'OnHit',
            FOREIGN KEY (move_id) REFERENCES moves(id) ON DELETE CASCADE,
            FOREIGN KEY (effect_id) REFERENCES move_effects(id) ON DELETE CASCADE,
            UNIQUE (move_id, effect_id, effect_order)
        )
        ''')
        
        # Create pokemon table
        cursor.execute('''
        CREATE TABLE pokemon (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            type1 INTEGER NOT NULL,
            type2 INTEGER,
            hp INTEGER NOT NULL,
            attack INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            special_attack INTEGER NOT NULL,
            special_defense INTEGER NOT NULL,
            speed INTEGER NOT NULL,
            total_stats INTEGER NOT NULL,
            evolution_level INTEGER,
            exp_curve TEXT NOT NULL CHECK(exp_curve IN ('fast', 'medium-fast', 'medium', 'medium-slow', 'slow', 'fluctuating')) DEFAULT 'medium-fast',
            FOREIGN KEY (type1) REFERENCES types(id),
            FOREIGN KEY (type2) REFERENCES types(id)
        )
        ''')

    def _insert_types(self, cursor):
        """Insert all Pokemon types"""
        types = [
            (1, 'Normal'),
            (2, 'Fire'),
            (3, 'Water'),
            (4, 'Electric'),
            (5, 'Grass'),
            (6, 'Ice'),
            (7, 'Fighting'),
            (8, 'Poison'),
            (9, 'Ground'),
            (10, 'Flying'),
            (11, 'Psychic'),
            (12, 'Bug'),
            (13, 'Rock'),
            (14, 'Ghost'),
            (15, 'Dragon'),
            (16, 'Dark'),
            (17, 'Steel'),
            (18, 'Fairy')
        ]
        
        cursor.executemany('INSERT INTO types (id, name) VALUES (?, ?)', types)
        print(f"Successfully inserted {len(types)} types")

    def _insert_move_effects(self, cursor):
        """Insert all move effects"""
        effects = [
            # Status effects
            ('Burn 10%', '10% chance to inflict burn', 'STATUS', 'Burn', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Burn 20%', '20% chance to inflict burn', 'STATUS', 'Burn', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Burn 30%', '30% chance to inflict burn', 'STATUS', 'Burn', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Burn 50%', '50% chance to inflict burn', 'STATUS', 'Burn', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Burn 100%', 'Always burns target', 'STATUS', 'Burn', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Paralysis 10%', '10% chance to inflict paralysis', 'STATUS', 'Paralysis', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Paralysis 20%', '20% chance to inflict paralysis', 'STATUS', 'Paralysis', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Paralysis 25%', '25% chance to inflict paralysis', 'STATUS', 'Paralysis', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Paralysis 30%', '30% chance to inflict paralysis', 'STATUS', 'Paralysis', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Paralysis 100%', 'Always paralyzes target', 'STATUS', 'Paralysis', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Freeze 10%', '10% chance to inflict freeze', 'STATUS', 'Freeze', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Freeze 20%', '20% chance to inflict freeze', 'STATUS', 'Freeze', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Freeze 100%', 'Always freezes target', 'STATUS', 'Freeze', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Poison 10%', '10% chance to inflict poison', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Poison 30%', '30% chance to inflict poison', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Poison 100%', 'Always poisons target', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Sleep', 'Puts target to sleep', 'STATUS', 'Sleep', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Confusion', 'Confuses target', 'STATUS', 'Confusion', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Confusion 100%', 'Always confuses target', 'STATUS', 'Confusion', None, 0, 0, 0, 0, None, None, 'Target'),
            
            # Stat changes
            ('Raise Attack 1', 'Raises user Attack by 1 stage', 'STAT_CHANGE', 'None', 'Attack', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Attack 2', 'Raises user Attack by 2 stages', 'STAT_CHANGE', 'None', 'Attack', 2, 0, 0, 0, None, None, 'User'),
            ('Raise Defense 1', 'Raises user Defense by 1 stage', 'STAT_CHANGE', 'None', 'Defense', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Defense 2', 'Sharply raises Defense', 'STAT_CHANGE', 'None', 'Defense', 2, 0, 0, 0, None, None, 'User'),
            ('Raise SpAttack 1', 'Raises user Sp. Attack by 1 stage', 'STAT_CHANGE', 'None', 'SpAttack', 1, 0, 0, 0, None, None, 'User'),
            ('Raise SpAttack 2', 'Sharply raises Sp. Attack', 'STAT_CHANGE', 'None', 'SpAttack', 2, 0, 0, 0, None, None, 'User'),
            ('Raise SpDefense 1', 'Raises user Sp. Defense by 1 stage', 'STAT_CHANGE', 'None', 'SpDefense', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Speed 1', 'Raises user Speed by 1 stage', 'STAT_CHANGE', 'None', 'Speed', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Speed 2', 'Raises user Speed by 2 stages', 'STAT_CHANGE', 'None', 'Speed', 2, 0, 0, 0, None, None, 'User'),
            ('Raise All Stats 1', 'Raises all user stats by 1 stage', 'STAT_CHANGE', 'None', 'All', 1, 0, 0, 0, None, None, 'User'),
            ('Lower Attack 1', 'Lowers target Attack by 1 stage', 'STAT_CHANGE', 'None', 'Attack', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower Defense 1', 'Lowers target Defense by 1 stage', 'STAT_CHANGE', 'None', 'Defense', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower Defense 2', 'Sharply lowers Defense', 'STAT_CHANGE', 'None', 'Defense', -2, 0, 0, 0, None, None, 'Target'),
            ('Lower SpAttack 1', 'Lowers target Sp. Attack by 1 stage', 'STAT_CHANGE', 'None', 'SpAttack', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower SpAttack 2', 'Sharply lowers Sp. Attack', 'STAT_CHANGE', 'None', 'SpAttack', -2, 0, 0, 0, None, None, 'Target'),
            ('Lower SpDefense 1', 'Lowers target Sp. Defense by 1 stage', 'STAT_CHANGE', 'None', 'SpDefense', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower SpDefense 2', 'Sharply lowers Sp. Defense', 'STAT_CHANGE', 'None', 'SpDefense', -2, 0, 0, 0, None, None, 'Target'),
            ('Lower Speed 1', 'Lowers target Speed by 1 stage', 'STAT_CHANGE', 'None', 'Speed', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower Accuracy 1', 'Lowers target Accuracy by 1 stage', 'STAT_CHANGE', 'None', 'Accuracy', -1, 0, 0, 0, None, None, 'Target'),
            
            # Healing
            ('Heal 25%', 'Heals user by 25% of max HP', 'HEAL', 'None', None, 0, 25, 0, 0, None, None, 'User'),
            ('Heal 50%', 'Heals user by 50% of max HP', 'HEAL', 'None', None, 0, 50, 0, 0, None, None, 'User'),
            ('Drain 50%', 'Drains 50% of damage dealt', 'HEAL', 'None', None, 0, 50, 0, 0, None, None, 'User'),
            ('Drain 75%', 'Drains 75% of damage dealt', 'HEAL', 'None', None, 0, 75, 0, 0, None, None, 'User'),
            ('Cure Status', 'Cures status conditions', 'HEAL', 'None', None, 0, 0, 0, 0, None, None, 'UserSide'),
            
            # Recoil
            ('Recoil 25%', 'User takes 25% recoil damage', 'RECOIL', 'None', None, 0, 0, 0, 25, None, None, 'User'),
            ('Recoil 33%', 'User takes 33% recoil damage', 'RECOIL', 'None', None, 0, 0, 0, 33, None, None, 'User'),
            ('Recoil 50%', 'User takes 50% recoil damage', 'RECOIL', 'None', None, 0, 0, 0, 50, None, None, 'User'),
            
            # Weather
            ('Set Sun', 'Sets harsh sunlight for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Sun', None, 'Field'),
            ('Set Rain', 'Sets rain for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Rain', None, 'Field'),
            ('Set Sandstorm', 'Sets sandstorm for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Sandstorm', None, 'Field'),
            ('Set Hail', 'Sets hail for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Hail', None, 'Field'),
            
            # Special effects - INCLUDING Force Berry
            ('Flinch', 'Causes target to flinch', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Always Crit', 'Always results in a critical hit', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Priority +1', 'Increased priority', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Protect', 'Protects user from attacks', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Multi Hit 2', 'Hits 2 times', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Multi Hit 3', 'Hits 3 times', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Multi Hit 2-5', 'Hits 2-5 times', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Recharge Turn', 'User cannot move next turn', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Self HP Cost 50%', 'User loses 50% HP', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Ignore Redirection', 'Ignores moves like Follow Me', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Ignore Protection', 'Bypasses protection moves', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Ignore Stat Changes', 'Ignores target stat changes', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Nullify Ability', 'Nullifies target ability', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Item Dependent', 'Fails if target has no item', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Remove Item', 'Removes target held item', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Trap 4-5 Turns', 'Traps target for 4-5 turns', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Prevent Switching', 'Prevents target from switching out', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Force Switch', 'Forces target to switch out', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Switch Out', 'User switches out after attack', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Never Miss', 'Never misses', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Force Berry', 'Forces all Pokémon to eat berries', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'AllPokemon'),
            ('Change Type Water', 'Changes target type to Water', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Change Type Grass', 'Adds Grass type to target', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Change Type Fire Remove', 'User loses Fire type', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Change Type Normal to Electric', 'Changes Normal moves to Electric', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Field'),
            ('Change Type Fire Weakness', 'Makes target weak to Fire', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Damage Contact', 'Damages contact attackers', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Prevent Sound Moves', 'Prevents target from using sound moves', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Use Target Attack', 'Uses target Attack stat for damage', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Type Dependent', 'Only hits Pokémon sharing type with user', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Damage Doubling', 'Double power if used after specific move', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Pursuit Damage', 'Double power if target is switching out', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Raise Accuracy 1', 'Raises user Accuracy by 1 stage', 'STAT_CHANGE', 'None', 'Accuracy', 1, 0, 0, 0, None, None, 'User'),
            
            # Field effects
            ('Set Spikes', 'Sets spikes on opponent side', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'Spikes', 'TargetSide'),
            ('Set Toxic Spikes', 'Sets toxic spikes on opponent side', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'ToxicSpikes', 'TargetSide'),
            ('Set Stealth Rock', 'Sets stealth rocks on opponent side', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'StealthRock', 'TargetSide'),
            ('Court Change', 'Switches field effects with opponent', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'CourtChange', 'Field'),
            
            # Damage modifiers
            ('HP Scaling High', 'More power at higher HP', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Speed Dependent', 'Double power if user attacks first', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Stat Dependent Damage', 'Uses higher of Attack or Sp. Attack', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Terrain Dependent', 'Effect changes with active terrain', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Stat Boost Scaling', '+20 power per stat boost', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
        
        
        ]
        
        cursor.executemany('''
        INSERT INTO move_effects 
        (name, description, effect_type, status_condition, stat_to_change, stat_change_amount, 
         heal_percentage, heal_fixed_amount, recoil_percentage, weather_type, field_condition, effect_target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', effects)

    def _insert_moves(self, cursor):
        """Insert ALL 365 moves"""
        moves = [
            # Original moves (1-100)
            (1, 'Ember', 'Fire', 'Special', 25, 40, 100, True, False, 0, 'Normal', 'A weak fire attack that may burn.'),
            (2, 'Flamethrower', 'Fire', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'A powerful fire blast that may burn.'),
            (3, 'Fire Blast', 'Fire', 'Special', 5, 110, 85, True, False, 0, 'Normal', 'A devastating fire attack that may burn.'),
            (4, 'Fire Punch', 'Fire', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'A fiery punch that may burn.'),
            (5, 'Flare Blitz', 'Fire', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'A fiery charge that hurts the user.'),
            (6, 'Water Gun', 'Water', 'Special', 25, 40, 100, True, False, 0, 'Normal', 'Squirts water to attack.'),
            (7, 'Surf', 'Water', 'Special', 15, 90, 100, True, False, 0, 'All_Adjacent_Foes', 'A big wave that hits all adjacent foes.'),
            (8, 'Hydro Pump', 'Water', 'Special', 5, 110, 80, True, False, 0, 'Normal', 'A powerful water blast.'),
            (9, 'Scald', 'Water', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'Hot water that may burn.'),
            (10, 'Aqua Tail', 'Water', 'Physical', 10, 90, 90, True, True, 0, 'Normal', 'A powerful water-based tail attack.'),
            (11, 'Thunder Shock', 'Electric', 'Special', 30, 40, 100, True, False, 0, 'Normal', 'A weak electric shock.'),
            (12, 'Thunderbolt', 'Electric', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'A strong electric blast that may paralyze.'),
            (13, 'Thunder', 'Electric', 'Special', 10, 110, 70, True, False, 0, 'Normal', 'A devastating thunderbolt that may paralyze.'),
            (14, 'Thunder Punch', 'Electric', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'An electric punch that may paralyze.'),
            (15, 'Volt Tackle', 'Electric', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'An electric charge that hurts the user.'),
            (16, 'Vine Whip', 'Grass', 'Physical', 25, 45, 100, True, True, 0, 'Normal', 'Whips with vines to attack.'),
            (17, 'Razor Leaf', 'Grass', 'Physical', 25, 55, 95, True, False, 0, 'All_Adjacent_Foes', 'Sharp leaves with high crit ratio.'),
            (18, 'Solar Beam', 'Grass', 'Special', 10, 120, 100, True, False, 0, 'Normal', 'Charges turn 1, attacks turn 2.'),
            (19, 'Energy Ball', 'Grass', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (20, 'Seed Bomb', 'Grass', 'Physical', 15, 80, 100, True, False, 0, 'Normal', 'A barrage of hard seeds.'),
            (21, 'Ice Shard', 'Ice', 'Physical', 30, 40, 100, True, False, 1, 'Normal', 'An ice attack that strikes first.'),
            (22, 'Ice Beam', 'Ice', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'A freezing beam that may freeze.'),
            (23, 'Blizzard', 'Ice', 'Special', 5, 110, 70, True, False, 0, 'All_Adjacent_Foes', 'A blizzard that may freeze.'),
            (24, 'Ice Punch', 'Ice', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'An icy punch that may freeze.'),
            (25, 'Avalanche', 'Ice', 'Physical', 10, 60, 100, True, True, -4, 'Normal', 'Power doubles if user was hit.'),
            (26, 'Karate Chop', 'Fighting', 'Physical', 25, 50, 100, True, True, 0, 'Normal', 'High critical hit ratio.'),
            (27, 'Brick Break', 'Fighting', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'Breaks barriers like Reflect.'),
            (28, 'Close Combat', 'Fighting', 'Physical', 5, 120, 100, True, True, 0, 'Normal', 'Lowers user Defense and Sp. Defense.'),
            (29, 'Drain Punch', 'Fighting', 'Physical', 10, 75, 100, True, True, 0, 'Normal', 'User recovers half the damage.'),
            (30, 'Mach Punch', 'Fighting', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'A punch that strikes first.'),
            (31, 'Poison Sting', 'Poison', 'Physical', 35, 15, 100, True, True, 0, 'Normal', 'May poison the target.'),
            (32, 'Sludge', 'Poison', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'May poison the target.'),
            (33, 'Sludge Bomb', 'Poison', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'May poison the target.'),
            (34, 'Poison Jab', 'Poison', 'Physical', 20, 80, 100, True, True, 0, 'Normal', 'May poison the target.'),
            (35, 'Toxic', 'Poison', 'Status', 10, None, 90, False, False, 0, 'Normal', 'Badly poisons the target.'),
            (36, 'Mud Slap', 'Ground', 'Special', 10, 20, 100, True, False, 0, 'Normal', 'Lowers target accuracy.'),
            (37, 'Earthquake', 'Ground', 'Physical', 10, 100, 100, True, False, 0, 'All_Adjacent', 'Hits all adjacent Pokémon.'),
            (38, 'Earth Power', 'Ground', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (39, 'Dig', 'Ground', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Digs underground turn 1, attacks turn 2.'),
            (40, 'Bone Club', 'Ground', 'Physical', 20, 65, 85, True, False, 0, 'Normal', 'May cause flinching.'),
            (41, 'Wing Attack', 'Flying', 'Physical', 35, 60, 100, True, True, 0, 'Normal', 'Strikes with wings.'),
            (42, 'Drill Peck', 'Flying', 'Physical', 20, 80, 100, True, True, 0, 'Normal', 'A corkscrewing attack.'),
            (43, 'Brave Bird', 'Flying', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'User takes recoil damage.'),
            (44, 'Air Slash', 'Flying', 'Special', 15, 75, 95, True, False, 0, 'Normal', 'May cause flinching.'),
            (45, 'Hurricane', 'Flying', 'Special', 10, 110, 70, True, False, 0, 'Normal', 'May confuse the target.'),
            (46, 'Confusion', 'Psychic', 'Special', 25, 50, 100, True, False, 0, 'Normal', 'May confuse the target.'),
            (47, 'Psychic', 'Psychic', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (48, 'Psybeam', 'Psychic', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'May confuse the target.'),
            (49, 'Zen Headbutt', 'Psychic', 'Physical', 15, 80, 90, True, True, 0, 'Normal', 'May cause flinching.'),
            (50, 'Future Sight', 'Psychic', 'Special', 10, 120, 100, True, False, 0, 'Normal', 'Hits in 2 turns.'),
            (51, 'Bug Bite', 'Bug', 'Physical', 20, 60, 100, True, True, 0, 'Normal', 'Eats target berry.'),
            (52, 'Signal Beam', 'Bug', 'Special', 15, 75, 100, True, False, 0, 'Normal', 'May confuse the target.'),
            (53, 'X-Scissor', 'Bug', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Slashes with crossed claws.'),
            (54, 'Bug Buzz', 'Bug', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (55, 'U-turn', 'Bug', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'User switches out after attack.'),
            (56, 'Rock Throw', 'Rock', 'Physical', 15, 50, 90, True, False, 0, 'Normal', 'Throws a small rock.'),
            (57, 'Rock Slide', 'Rock', 'Physical', 10, 75, 90, True, False, 0, 'All_Adjacent_Foes', 'May cause flinching.'),
            (58, 'Stone Edge', 'Rock', 'Physical', 5, 100, 80, True, False, 0, 'Normal', 'High critical hit ratio.'),
            (59, 'Ancient Power', 'Rock', 'Special', 5, 60, 100, True, False, 0, 'Normal', 'May raise all user stats.'),
            (60, 'Power Gem', 'Rock', 'Special', 20, 80, 100, True, False, 0, 'Normal', 'Attacks with a ray of light.'),
            (61, 'Lick', 'Ghost', 'Physical', 30, 30, 100, True, True, 0, 'Normal', 'May paralyze the target.'),
            (62, 'Shadow Ball', 'Ghost', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (63, 'Shadow Claw', 'Ghost', 'Physical', 15, 70, 100, True, True, 0, 'Normal', 'High critical hit ratio.'),
            (64, 'Shadow Punch', 'Ghost', 'Physical', 20, 60, 100, True, True, 0, 'Normal', 'Never misses.'),
            (65, 'Hex', 'Ghost', 'Special', 10, 65, 100, True, False, 0, 'Normal', 'Double power if target has status.'),
            (66, 'Dragon Breath', 'Dragon', 'Special', 20, 60, 100, True, False, 0, 'Normal', 'May paralyze the target.'),
            (67, 'Dragon Claw', 'Dragon', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Slash with sharp claws.'),
            (68, 'Dragon Pulse', 'Dragon', 'Special', 10, 85, 100, True, False, 0, 'Normal', 'A powerful dragon pulse.'),
            (69, 'Outrage', 'Dragon', 'Physical', 10, 120, 100, True, True, 0, 'Normal', 'User attacks for 2-3 turns then confuses.'),
            (70, 'Dragon Rush', 'Dragon', 'Physical', 10, 100, 75, True, True, 0, 'Normal', 'May cause flinching.'),
            (71, 'Bite', 'Dark', 'Physical', 25, 60, 100, True, True, 0, 'Normal', 'May cause flinching.'),
            (72, 'Crunch', 'Dark', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'May lower target Defense.'),
            (73, 'Dark Pulse', 'Dark', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'May cause flinching.'),
            (74, 'Night Slash', 'Dark', 'Physical', 15, 70, 100, True, True, 0, 'Normal', 'High critical hit ratio.'),
            (75, 'Sucker Punch', 'Dark', 'Physical', 5, 70, 100, True, True, 1, 'Normal', 'Strikes first if target attacks.'),
            (76, 'Metal Claw', 'Steel', 'Physical', 35, 50, 95, True, True, 0, 'Normal', 'May raise user Attack.'),
            (77, 'Iron Head', 'Steel', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'May cause flinching.'),
            (78, 'Flash Cannon', 'Steel', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (79, 'Meteor Mash', 'Steel', 'Physical', 10, 90, 90, True, True, 0, 'Normal', 'May raise user Attack.'),
            (80, 'Bullet Punch', 'Steel', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'A punch that strikes first.'),
            (81, 'Fairy Wind', 'Fairy', 'Special', 30, 40, 100, True, False, 0, 'Normal', 'Stirs up a fairy wind.'),
            (82, 'Dazzling Gleam', 'Fairy', 'Special', 10, 80, 100, True, False, 0, 'All_Adjacent_Foes', 'Damages all adjacent foes.'),
            (83, 'Moonblast', 'Fairy', 'Special', 15, 95, 100, True, False, 0, 'Normal', 'May lower target Sp. Attack.'),
            (84, 'Play Rough', 'Fairy', 'Physical', 10, 90, 90, True, True, 0, 'Normal', 'May lower target Attack.'),
            (85, 'Spirit Break', 'Fairy', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'Lowers target Sp. Attack.'),
            (86, 'Tackle', 'Normal', 'Physical', 35, 40, 100, True, True, 0, 'Normal', 'A basic physical attack.'),
            (87, 'Headbutt', 'Normal', 'Physical', 15, 70, 100, True, True, 0, 'Normal', 'May cause flinching.'),
            (88, 'Body Slam', 'Normal', 'Physical', 15, 85, 100, True, True, 0, 'Normal', 'May paralyze the target.'),
            (89, 'Hyper Beam', 'Normal', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'User must recharge next turn.'),
            (90, 'Giga Impact', 'Normal', 'Physical', 5, 150, 90, True, True, 0, 'Normal', 'User must recharge next turn.'),
            (91, 'Swords Dance', 'Normal', 'Status', 20, None, None, False, False, 0, 'Self', 'Sharply raises user Attack.'),
            (92, 'Calm Mind', 'Psychic', 'Status', 20, None, None, False, False, 0, 'Self', 'Raises user Sp. Attack and Sp. Defense.'),
            (93, 'Thunder Wave', 'Electric', 'Status', 20, None, 90, False, False, 0, 'Normal', 'Paralyzes the target.'),
            (94, 'Will-O-Wisp', 'Fire', 'Status', 15, None, 85, False, False, 0, 'Normal', 'Burns the target.'),
            (95, 'Toxic Spikes', 'Poison', 'Status', 20, None, None, False, False, 0, 'Opponents_Field', 'Sets toxic spikes on opponent side.'),
            (96, 'Stealth Rock', 'Rock', 'Status', 20, None, None, False, False, 0, 'Opponents_Field', 'Sets stealth rocks on opponent side.'),
            (97, 'Reflect', 'Psychic', 'Status', 20, None, None, False, False, 0, 'UserSide', 'Reduces physical damage for 5 turns.'),
            (98, 'Light Screen', 'Psychic', 'Status', 30, None, None, False, False, 0, 'UserSide', 'Reduces special damage for 5 turns.'),
            (99, 'Recover', 'Normal', 'Status', 10, None, None, False, False, 0, 'Self', 'Restores 50% of max HP.'),
            (100, 'Roar', 'Normal', 'Status', 20, None, None, False, False, -6, 'Normal', 'Forces target to switch out.'),

            # NEW FIRE MOVES (101-115)
            (101, 'Blue Flare', 'Fire', 'Special', 5, 130, 85, True, False, 0, 'Normal', 'A high-damage fire attack that may burn.'),
            (102, 'Sacred Fire', 'Fire', 'Physical', 5, 100, 95, True, False, 0, 'Normal', 'A mystical fire attack that may burn.'),
            (103, 'Inferno', 'Fire', 'Special', 5, 100, 50, True, False, 0, 'Normal', 'Always burns if it hits.'),
            (104, 'Heat Wave', 'Fire', 'Special', 10, 95, 90, True, False, 0, 'All_Adjacent_Foes', 'May burn adjacent foes.'),
            (105, 'Mystical Fire', 'Fire', 'Special', 10, 75, 100, True, False, 0, 'Normal', 'Lowers target Sp. Attack.'),
            (106, 'Shell Trap', 'Fire', 'Special', 5, 150, 100, True, False, -3, 'All_Adjacent_Foes', 'User takes damage if hit before attacking.'),
            (107, 'Mind Blown', 'Fire', 'Special', 5, 150, 100, True, False, 0, 'All_Adjacent', 'User loses 50% HP.'),
            (108, 'Burn Up', 'Fire', 'Special', 5, 130, 100, True, False, 0, 'Normal', 'User loses Fire type after use.'),
            (109, 'Flame Charge', 'Fire', 'Physical', 20, 50, 100, True, True, 0, 'Normal', 'Raises user Speed.'),
            (110, 'Incinerate', 'Fire', 'Special', 15, 60, 100, True, False, 0, 'All_Adjacent_Foes', 'Destroys target berry.'),
            (111, 'Fire Lash', 'Fire', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Lowers target Defense.'),
            (112, 'Pyro Ball', 'Fire', 'Physical', 5, 120, 90, True, False, 0, 'Normal', 'May burn target.'),
            (113, 'Fire Fang', 'Fire', 'Physical', 15, 65, 95, True, True, 0, 'Normal', 'May burn or cause flinching.'),
            (114, 'Blast Burn', 'Fire', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'User must recharge next turn.'),
            (115, 'Overheat', 'Fire', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Sharply lowers user Sp. Attack.'),

            # NEW WATER MOVES (116-130)
            (116, 'Origin Pulse', 'Water', 'Special', 10, 110, 85, True, False, 0, 'All_Adjacent_Foes', 'Legendary water pulse attack.'),
            (117, 'Water Spout', 'Water', 'Special', 5, 150, 100, True, False, 0, 'All_Adjacent_Foes', 'More power at higher HP.'),
            (118, 'Fishious Rend', 'Water', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'Double power if user attacks first.'),
            (119, 'Snipe Shot', 'Water', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'High critical hit ratio, ignores redirection.'),
            (120, 'Dual Chop', 'Dragon', 'Physical', 15, 40, 90, True, True, 0, 'Normal', 'Hits twice in one turn.'),
            (121, 'Octazooka', 'Water', 'Special', 10, 65, 85, True, False, 0, 'Normal', 'May lower target accuracy.'),
            (122, 'Soak', 'Water', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Changes target type to Water.'),
            (123, 'Water Pledge', 'Water', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Combines with other pledge moves.'),
            (124, 'Crabhammer', 'Water', 'Physical', 10, 100, 90, True, True, 0, 'Normal', 'High critical hit ratio.'),
            (125, 'Razor Shell', 'Water', 'Physical', 10, 75, 95, True, True, 0, 'Normal', 'May lower target Defense.'),
            (126, 'Waterfall', 'Water', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'May cause flinching.'),
            (127, 'Liquidation', 'Water', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'May lower target Defense.'),
            (128, 'Bubble Beam', 'Water', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'May lower target Speed.'),
            (129, 'Whirlpool', 'Water', 'Special', 15, 35, 85, True, False, 0, 'Normal', 'Traps target for 4-5 turns.'),
            (130, 'Brine', 'Water', 'Special', 10, 65, 100, True, False, 0, 'Normal', 'Double power if target HP is half or less.'),

            # NEW ELECTRIC MOVES (131-145)
            (131, 'Bolt Strike', 'Electric', 'Physical', 5, 130, 85, True, True, 0, 'Normal', 'May paralyze target.'),
            (132, 'Plasma Fists', 'Electric', 'Physical', 15, 100, 100, True, True, 0, 'Normal', 'Changes Normal moves to Electric this turn.'),
            (133, 'Zap Cannon', 'Electric', 'Special', 5, 120, 50, True, False, 0, 'Normal', 'Always paralyzes if it hits.'),
            (134, 'Rising Voltage', 'Electric', 'Special', 20, 70, 100, True, False, 0, 'Normal', 'Double power on Electric Terrain.'),
            (135, 'Aura Wheel', 'Electric', 'Physical', 10, 110, 100, True, False, 0, 'Normal', 'Raises user Speed.'),
            (136, 'Parabolic Charge', 'Electric', 'Special', 20, 65, 100, True, False, 0, 'All_Adjacent', 'User recovers 50% of damage dealt.'),
            (137, 'Electro Ball', 'Electric', 'Special', 10, None, 100, True, False, 0, 'Normal', 'More power the faster user is than target.'),
            (138, 'Volt Switch', 'Electric', 'Special', 20, 70, 100, True, False, 0, 'Normal', 'User switches out after attack.'),
            (139, 'Discharge', 'Electric', 'Special', 15, 80, 100, True, False, 0, 'All_Adjacent', 'May paralyze adjacent Pokémon.'),
            (140, 'Wild Charge', 'Electric', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'User takes recoil damage.'),
            (141, 'Fusion Bolt', 'Electric', 'Physical', 5, 100, 100, True, True, 0, 'Normal', 'Power doubles if used after Fusion Flare.'),
            (142, 'Bolt Beak', 'Electric', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'Double power if user attacks first.'),
            (143, 'Zing Zap', 'Electric', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'May cause flinching.'),
            (144, 'Nuzzle', 'Electric', 'Physical', 20, 20, 100, True, True, 0, 'Normal', 'Paralyzes target.'),
            (145, 'Magnetic Flux', 'Electric', 'Status', 20, None, None, False, False, 0, 'UserSide', 'Raises Defense and Sp. Defense of Plus/Minus Pokémon.'),

            # NEW GRASS MOVES (146-160)
            (146, 'Leaf Storm', 'Grass', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Sharply lowers user Sp. Attack.'),
            (147, 'Power Whip', 'Grass', 'Physical', 10, 120, 85, True, True, 0, 'Normal', 'A powerful whipping attack.'),
            (148, 'Horn Leech', 'Grass', 'Physical', 10, 75, 100, True, True, 0, 'Normal', 'User recovers 50% of damage dealt.'),
            (149, 'Forests Curse', 'Grass', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Adds Grass type to target.'),
            (150, 'Grassy Glide', 'Grass', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'Priority on Grassy Terrain.'),
            (151, 'Leaf Blade', 'Grass', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'High critical hit ratio.'),
            (152, 'Wood Hammer', 'Grass', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'User takes recoil damage.'),
            (153, 'Seed Flare', 'Grass', 'Special', 5, 120, 85, True, False, 0, 'Normal', 'May sharply lower target Sp. Defense.'),
            (154, 'Apple Acid', 'Grass', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Lowers target Sp. Defense.'),
            (155, 'Grav Apple', 'Grass', 'Physical', 10, 80, 100, True, False, 0, 'Normal', 'Lowers target Defense.'),
            (156, 'Drum Beating', 'Grass', 'Physical', 10, 80, 100, True, False, 0, 'Normal', 'Lowers target Speed.'),
            (157, 'Branch Poke', 'Grass', 'Physical', 40, 40, 100, True, True, 0, 'Normal', 'A quick physical attack.'),
            (158, 'Needle Arm', 'Grass', 'Physical', 15, 60, 100, True, True, 0, 'Normal', 'May cause flinching.'),
            (159, 'Spiky Shield', 'Grass', 'Status', 10, None, None, False, False, 4, 'Self', 'Protects and damages contact attackers.'),
            (160, 'Cotton Guard', 'Grass', 'Status', 10, None, None, False, False, 0, 'Self', 'Sharply raises user Defense.'),

            # NEW PSYCHIC MOVES (161-175)
            (161, 'Photon Geyser', 'Psychic', 'Special', 5, 100, 100, True, False, 0, 'Normal', 'Uses higher of Attack or Sp. Attack.'),
            (162, 'Prismatic Laser', 'Psychic', 'Special', 10, 160, 100, True, False, 0, 'Normal', 'User cannot move next turn.'),
            (163, 'Psycho Boost', 'Psychic', 'Special', 5, 140, 90, True, False, 0, 'Normal', 'Sharply lowers user Sp. Attack.'),
            (164, 'Stored Power', 'Psychic', 'Special', 10, 20, 100, True, False, 0, 'Normal', '+20 power for each stat boost.'),
            (165, 'Expanding Force', 'Psychic', 'Special', 10, 80, 100, True, False, 0, 'All_Adjacent_Foes', 'Hits all foes on Psychic Terrain.'),
            (166, 'Freezing Glare', 'Psychic', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'May freeze target.'),
            (167, 'Psystrike', 'Psychic', 'Special', 10, 100, 100, True, False, 0, 'Normal', 'Uses target Defense instead of Sp. Defense.'),
            (168, 'Synchronoise', 'Psychic', 'Special', 10, 120, 100, True, False, 0, 'All_Adjacent', 'Hits only Pokémon sharing a type with user.'),
            (169, 'Miracle Eye', 'Psychic', 'Status', 40, None, None, False, False, 0, 'Normal', 'Allows Psychic moves to hit Dark types.'),
            (170, 'Heart Stamp', 'Psychic', 'Physical', 25, 60, 100, True, True, 0, 'Normal', 'May cause flinching.'),
            (171, 'Hyperspace Hole', 'Psychic', 'Special', 5, 80, None, True, False, 0, 'Normal', 'Bypasses protection and never misses.'),
            (172, 'Hyperspace Fury', 'Dark', 'Physical', 5, 100, None, True, False, 0, 'Normal', 'Bypasses protection, lowers user Defense.'),
            (173, 'Luster Purge', 'Psychic', 'Special', 5, 70, 100, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (174, 'Mist Ball', 'Psychic', 'Special', 5, 70, 100, True, False, 0, 'Normal', 'May lower target Sp. Attack.'),
            (175, 'Speed Swap', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Swaps Speed stat with target.'),

            # NEW DARK MOVES (176-190)
            (176, 'Wicked Blow', 'Dark', 'Physical', 5, 80, 100, True, True, 0, 'Normal', 'Always results in a critical hit.'),
            (177, 'Fiery Wrath', 'Dark', 'Special', 10, 90, 100, True, False, 0, 'All_Adjacent_Foes', 'May cause flinching.'),
            (178, 'False Surrender', 'Dark', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Never misses.'),
            (179, 'Obstruct', 'Dark', 'Status', 10, None, 100, False, False, 4, 'Self', 'Protects user and lowers Defense of attacker.'),
            (180, 'Jaw Lock', 'Dark', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Prevents switching for both Pokémon.'),
            (181, 'Throat Chop', 'Dark', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Prevents target from using sound moves.'),
            (182, 'Darkest Lariat', 'Dark', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'Ignores target stat changes.'),
            (183, 'Knock Off', 'Dark', 'Physical', 20, 65, 100, True, True, 0, 'Normal', 'Removes target held item.'),
            (184, 'Pursuit', 'Dark', 'Physical', 20, 40, 100, True, True, 0, 'Normal', 'Double power if target is switching out.'),
            (185, 'Snarl', 'Dark', 'Special', 15, 55, 95, True, False, 0, 'All_Adjacent_Foes', 'Lowers target Sp. Attack.'),
            (186, 'Foul Play', 'Dark', 'Physical', 15, 95, 100, True, True, 0, 'Normal', 'Uses target Attack stat.'),
            (187, 'Parting Shot', 'Dark', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Lowers target Attack and Sp. Attack, user switches.'),
            (188, 'Taunt', 'Dark', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Prevents target from using status moves.'),
            (189, 'Nasty Plot', 'Dark', 'Status', 20, None, None, False, False, 0, 'Self', 'Sharply raises user Sp. Attack.'),
            (190, 'Hone Claws', 'Dark', 'Status', 15, None, None, False, False, 0, 'Self', 'Raises user Attack and Accuracy.'),

            # NEW DRAGON MOVES (191-205)
            (191, 'Dragon Energy', 'Dragon', 'Special', 5, 150, 100, True, False, 0, 'All_Adjacent_Foes', 'More power at higher HP.'),
            (192, 'Eternabeam', 'Dragon', 'Special', 5, 160, 90, True, False, 0, 'Normal', 'User cannot move next turn.'),
            (193, 'Clanging Scales', 'Dragon', 'Special', 5, 110, 100, True, False, 0, 'All_Adjacent_Foes', 'Lowers user Defense.'),
            (194, 'Core Enforcer', 'Dragon', 'Special', 10, 100, 100, True, False, 0, 'All_Adjacent_Foes', 'Nullifies abilities of targets.'),
            (195, 'Dragon Darts', 'Dragon', 'Physical', 10, 50, 100, True, False, 0, 'Normal', 'Hits twice, can target different foes.'),
            (196, 'Dragon Hammer', 'Dragon', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'User slams target with body.'),
            (197, 'Dragon Tail', 'Dragon', 'Physical', 10, 60, 90, True, True, -6, 'Normal', 'Forces target to switch out.'),
            (198, 'Breaking Swipe', 'Dragon', 'Physical', 15, 60, 100, True, True, 0, 'All_Adjacent_Foes', 'Lowers target Attack.'),
            (199, 'Scale Shot', 'Dragon', 'Physical', 20, 25, 90, True, False, 0, 'Normal', 'Hits 2-5 times, raises Speed, lowers Defense.'),
            (200, 'Dual Wingbeat', 'Flying', 'Physical', 10, 40, 90, True, True, 0, 'Normal', 'Hits twice in one turn.'),
            (201, 'Dragon Dance', 'Dragon', 'Status', 20, None, None, False, False, 0, 'Self', 'Raises user Attack and Speed.'),
            (202, 'Roar of Time', 'Dragon', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'User must recharge next turn.'),
            (203, 'Spacial Rend', 'Dragon', 'Special', 5, 100, 95, True, False, 0, 'Normal', 'High critical hit ratio.'),
            (204, 'Draco Meteor', 'Dragon', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Sharply lowers user Sp. Attack.'),
            (205, 'Dragon Ascent', 'Flying', 'Physical', 5, 120, 100, True, True, 0, 'Normal', 'Lowers user Defense and Sp. Defense.'),

            # NEW FAIRY MOVES (206-220)
            (206, 'Fleur Cannon', 'Fairy', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Sharply lowers user Sp. Attack.'),
            (207, 'Light That Burns The Sky', 'Fairy', 'Special', 1, 200, 100, True, False, 0, 'Normal', 'Uses higher of Attack or Sp. Attack.'),
            (208, 'Strange Steam', 'Fairy', 'Special', 10, 90, 95, True, False, 0, 'Normal', 'May confuse target.'),
            (209, 'Decorate', 'Fairy', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Sharply raises target Attack and Sp. Attack.'),
            (210, 'Draining Kiss', 'Fairy', 'Special', 10, 50, 100, True, False, 0, 'Normal', 'User recovers 75% of damage dealt.'),
            (211, 'Play Nice', 'Fairy', 'Status', 20, None, None, False, False, 0, 'Normal', 'Lowers target Attack.'),
            (212, 'Fairy Lock', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Field', 'Prevents switching next turn.'),
            (213, 'Crafty Shield', 'Fairy', 'Status', 10, None, None, False, False, 3, 'UserSide', 'Protects from status moves.'),
            (214, 'Flower Shield', 'Fairy', 'Status', 10, None, None, False, False, 0, 'All', 'Raises Defense of Grass-type Pokémon.'),
            (215, 'Aromatic Mist', 'Fairy', 'Status', 20, None, None, False, False, 0, 'Adjacent_Ally', 'Raises ally Sp. Defense.'),
            (216, 'Baby-Doll Eyes', 'Fairy', 'Status', 30, None, 100, False, False, 1, 'Normal', 'Lowers target Attack. Priority +1.'),
            (217, 'Geomancy', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Self', 'Charges turn 1, sharply raises Sp. Attack, Sp. Defense, Speed turn 2.'),
            (218, 'Misty Explosion', 'Fairy', 'Special', 5, 100, 100, True, False, 0, 'All_Adjacent', 'User faints. Power increased in Misty Terrain.'),
            (219, 'Nature Madness', 'Fairy', 'Special', 10, None, 90, True, False, 0, 'Normal', 'Reduces target HP by half.'),
            (220, 'Sweet Kiss', 'Fairy', 'Status', 10, None, 75, False, False, 0, 'Normal', 'Confuses target.'),

            # NEW FIGHTING MOVES (221-235)
            (221, 'No Retreat', 'Fighting', 'Status', 5, None, 100, False, False, 0, 'Self', 'Raises all stats but cannot switch out.'),
            (222, 'Thunderous Kick', 'Fighting', 'Physical', 10, 90, 100, True, True, 0, 'Normal', 'Lowers target Defense.'),
            (223, 'Victory Dance', 'Fighting', 'Status', 10, None, 100, False, False, 0, 'Self', 'Raises Attack, Defense, Speed.'),
            (224, 'Triple Arrows', 'Fighting', 'Physical', 10, 90, 100, True, False, 0, 'Normal', 'High crit, may lower Defense or flinch.'),
            (225, 'Aura Sphere', 'Fighting', 'Special', 20, 80, None, True, False, 0, 'Normal', 'Never misses.'),
            (226, 'Focus Blast', 'Fighting', 'Special', 5, 120, 70, True, False, 0, 'Normal', 'May lower target Sp. Defense.'),
            (227, 'Vacuum Wave', 'Fighting', 'Special', 30, 40, 100, True, False, 1, 'Normal', 'Priority +1.'),
            (228, 'Secret Sword', 'Fighting', 'Special', 10, 85, 100, True, False, 0, 'Normal', 'Uses target Defense instead of Sp. Defense.'),
            (229, 'Surging Strikes', 'Water', 'Physical', 5, 25, 100, True, True, 0, 'Normal', 'Hits 3 times, always critical.'),
            (230, 'Coaching', 'Fighting', 'Status', 10, None, None, False, False, 0, 'Adjacent_Ally', 'Raises ally Attack and Defense.'),
            (231, 'Body Press', 'Fighting', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Uses user Defense instead of Attack.'),
            (232, 'Revenge', 'Fighting', 'Physical', 10, 60, 100, True, True, -4, 'Normal', 'Double power if user was hit.'),
            (233, 'Counter', 'Fighting', 'Physical', 20, None, 100, True, True, -5, 'Normal', 'Returns double the physical damage taken.'),
            (234, 'Dynamic Punch', 'Fighting', 'Physical', 5, 100, 50, True, True, 0, 'Normal', 'Always confuses if it hits.'),
            (235, 'Cross Chop', 'Fighting', 'Physical', 5, 100, 80, True, True, 0, 'Normal', 'High critical hit ratio.'),

            # NEW GHOST MOVES (236-250)
            (236, 'Astral Barrage', 'Ghost', 'Special', 5, 120, 100, True, False, 0, 'All_Adjacent_Foes', 'Legendary ghostly attack.'),
            (237, 'Poltergeist', 'Ghost', 'Physical', 5, 110, 90, True, False, 0, 'Normal', 'Fails if target has no item.'),
            (238, 'Spirit Shackle', 'Ghost', 'Physical', 10, 80, 100, True, False, 0, 'Normal', 'Prevents target from switching.'),
            (239, 'Shadow Bone', 'Ghost', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'May lower target Defense.'),
            (240, 'Moongeist Beam', 'Ghost', 'Special', 5, 100, 100, True, False, 0, 'Normal', 'Ignores target ability.'),
            (241, 'Spectral Thief', 'Ghost', 'Physical', 10, 90, 100, True, True, 0, 'Normal', 'Steals target stat boosts.'),
            (242, 'Trick-or-Treat', 'Ghost', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Adds Ghost type to target.'),
            (243, 'Phantom Force', 'Ghost', 'Physical', 10, 90, 100, True, True, 0, 'Normal', 'Disappears turn 1, attacks turn 2.'),
            (244, 'Ominous Wind', 'Ghost', 'Special', 5, 60, 100, True, False, 0, 'Normal', 'May raise all user stats.'),
            (245, 'Grudge', 'Ghost', 'Status', 5, None, None, False, False, 0, 'Self', 'If user faints, deletes PP of move that KOed it.'),
            (246, 'Destiny Bond', 'Ghost', 'Status', 5, None, None, False, False, 0, 'Self', 'If user faints, attacker also faints.'),
            (247, 'Curse', 'Ghost', 'Status', 10, None, None, False, False, 0, 'Normal', 'Ghosts lose 50% HP, others lower Speed and raise Attack/Defense.'),
            (248, 'Night Shade', 'Ghost', 'Special', 15, None, 100, True, False, 0, 'Normal', 'Deals damage equal to user level.'),
            (249, 'Shadow Sneak', 'Ghost', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'Priority +1.'),
            (250, 'Infernal Parade', 'Ghost', 'Special', 15, 60, 100, True, False, 0, 'Normal', 'Double power if target has status.'),

            # NEW ICE MOVES (251-265)
            (251, 'Glacial Lance', 'Ice', 'Physical', 5, 120, 100, True, False, 0, 'All_Adjacent_Foes', 'Legendary ice spear attack.'),
            (252, 'Triple Axel', 'Ice', 'Physical', 10, 20, 90, True, True, 0, 'Normal', 'Hits 3 times, power increases each hit.'),
            (253, 'Freeze-Dry', 'Ice', 'Special', 20, 70, 100, True, False, 0, 'Normal', 'Super effective against Water types.'),
            (254, 'Ice Hammer', 'Ice', 'Physical', 10, 100, 90, True, True, 0, 'Normal', 'Lowers user Speed.'),
            (255, 'Aurora Veil', 'Ice', 'Status', 20, None, None, False, False, 0, 'UserSide', 'Halves damage from Physical and Special moves in hail.'),
            (256, 'Sheer Cold', 'Ice', 'Special', 5, None, 30, True, False, 0, 'Normal', 'One-hit KO if it hits.'),
            (257, 'Ice Burn', 'Ice', 'Special', 5, 140, 90, True, False, 0, 'Normal', 'Charges turn 1, may burn turn 2.'),
            (258, 'Freeze Shock', 'Ice', 'Physical', 5, 140, 90, True, False, 0, 'Normal', 'Charges turn 1, may paralyze turn 2.'),
            (259, 'Frost Breath', 'Ice', 'Special', 10, 60, 90, True, False, 0, 'Normal', 'Always results in a critical hit.'),
            (260, 'Icicle Crash', 'Ice', 'Physical', 10, 85, 90, True, False, 0, 'Normal', 'May cause flinching.'),
            (261, 'Icicle Spear', 'Ice', 'Physical', 30, 25, 100, True, False, 0, 'Normal', 'Hits 2-5 times.'),
            (262, 'Aurora Beam', 'Ice', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'May lower target Attack.'),
            (263, 'Mist', 'Ice', 'Status', 30, None, None, False, False, 0, 'UserSide', 'Prevents stat reduction for 5 turns.'),
            (264, 'Haze', 'Ice', 'Status', 30, None, None, False, False, 0, 'All', 'Resets all stat changes.'),
            (265, 'Powder Snow', 'Ice', 'Special', 25, 40, 100, True, False, 0, 'All_Adjacent_Foes', 'May freeze adjacent foes.'),

            # NEW ROCK MOVES (266-280)
            (266, 'Diamond Storm', 'Rock', 'Physical', 5, 100, 95, True, False, 0, 'All_Adjacent_Foes', 'May raise user Defense.'),
            (267, 'Tar Shot', 'Rock', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Lowers Speed and makes target weak to Fire.'),
            (268, 'Rock Wrecker', 'Rock', 'Physical', 5, 150, 90, True, False, 0, 'Normal', 'User must recharge next turn.'),
            (269, 'Head Smash', 'Rock', 'Physical', 5, 150, 80, True, True, 0, 'Normal', 'User takes heavy recoil damage.'),
            (270, 'Rock Blast', 'Rock', 'Physical', 10, 25, 90, True, False, 0, 'Normal', 'Hits 2-5 times.'),
            (271, 'Rock Polish', 'Rock', 'Status', 20, None, None, False, False, 0, 'Self', 'Sharply raises user Speed.'),
            (272, 'Smack Down', 'Rock', 'Physical', 15, 50, 100, True, False, 0, 'Normal', 'Makes Flying types vulnerable to Ground.'),
            (273, 'Wide Guard', 'Rock', 'Status', 10, None, None, False, False, 3, 'UserSide', 'Protects from spread moves.'),
            (274, 'Accelerock', 'Rock', 'Physical', 20, 40, 100, True, True, 1, 'Normal', 'Priority +1.'),
            (275, 'Meteor Beam', 'Rock', 'Special', 10, 120, 90, True, False, 0, 'Normal', 'Charges turn 1, raises Sp. Attack.'),
            (276, 'Continental Crush', 'Rock', 'Physical', 1, None, None, True, False, 0, 'Normal', 'Z-Move. Varies with base move.'),
            (277, 'Tectonic Rage', 'Ground', 'Physical', 1, None, None, True, False, 0, 'Normal', 'Z-Move. Varies with base move.'),
            (278, 'Corkscrew Crash', 'Steel', 'Physical', 1, None, None, True, False, 0, 'Normal', 'Z-Move. Varies with base move.'),
            (279, 'Inferno Overdrive', 'Fire', 'Special', 1, None, None, True, False, 0, 'Normal', 'Z-Move. Varies with base move.'),
            (280, 'Hydro Vortex', 'Water', 'Physical', 1, None, None, True, False, 0, 'Normal', 'Z-Move. Varies with base move.'),

            # NEW STEEL MOVES (281-295)
            (281, 'Steel Beam', 'Steel', 'Special', 5, 140, 95, True, False, 0, 'Normal', 'User loses 50% HP.'),
            (282, 'Double Iron Bash', 'Steel', 'Physical', 5, 60, 100, True, True, 0, 'Normal', 'Hits twice, may cause flinching.'),
            (283, 'Sunsteel Strike', 'Steel', 'Physical', 5, 100, 100, True, True, 0, 'Normal', 'Ignores target ability.'),
            # Removed duplicate Moongeist Beam (284) - already exists as ID 240
            (285, 'Gear Grind', 'Steel', 'Physical', 15, 50, 85, True, True, 0, 'Normal', 'Hits twice in one turn.'),
            (286, 'Anchor Shot', 'Steel', 'Physical', 20, 80, 100, True, True, 0, 'Normal', 'Prevents target from switching.'),
            (287, 'Kings Shield', 'Steel', 'Status', 10, None, None, False, False, 4, 'Self', 'Protects and lowers Attack of contact attackers.'),
            (288, 'Smart Strike', 'Steel', 'Physical', 10, 70, None, True, True, 0, 'Normal', 'Never misses.'),
            (289, 'Behemoth Blade', 'Steel', 'Physical', 5, 100, 100, True, True, 0, 'Normal', 'Double power against Dynamax Pokémon.'),
            (290, 'Behemoth Bash', 'Steel', 'Physical', 5, 100, 100, True, True, 0, 'Normal', 'Double power against Dynamax Pokémon.'),
            (291, 'Steel Roller', 'Steel', 'Physical', 5, 130, 100, True, True, 0, 'Normal', 'Destroys terrain, fails if no terrain.'),
            (292, 'Magnet Bomb', 'Steel', 'Physical', 20, 60, None, True, False, 0, 'Normal', 'Never misses.'),
            (293, 'Mirror Shot', 'Steel', 'Special', 10, 65, 85, True, False, 0, 'Normal', 'May lower target accuracy.'),
            (294, 'Shift Gear', 'Steel', 'Status', 10, None, None, False, False, 0, 'Self', 'Raises user Attack and sharply raises Speed.'),
            (295, 'Iron Defense', 'Steel', 'Status', 15, None, None, False, False, 0, 'Self', 'Sharply raises user Defense.'),

            # NEW BUG MOVES (296-310)
            (296, 'Attack Order', 'Bug', 'Physical', 15, 90, 100, True, False, 0, 'Normal', 'High critical hit ratio.'),
            (297, 'Skitter Smack', 'Bug', 'Physical', 10, 70, 90, True, True, 0, 'Normal', 'Lowers target Sp. Attack.'),
            (298, 'First Impression', 'Bug', 'Physical', 10, 90, 100, True, True, 2, 'Normal', 'Priority +2, only works first turn user is out.'),
            (299, 'Pollen Puff', 'Bug', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'Heals ally if targeted at them.'),
            (300, 'Lunge', 'Bug', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Lowers target Attack.'),
            (301, 'Leech Life', 'Bug', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'User recovers 50% of damage dealt.'),
            (302, 'Fell Stinger', 'Bug', 'Physical', 25, 50, 100, True, True, 0, 'Normal', 'Sharply raises Attack if KOes target.'),
            (303, 'Quiver Dance', 'Bug', 'Status', 20, None, None, False, False, 0, 'Self', 'Raises Sp. Attack, Sp. Defense, and Speed.'),
            # Removed duplicate Bug Bite (304) - already exists as ID 51
            (305, 'Silver Wind', 'Bug', 'Special', 5, 60, 100, True, False, 0, 'Normal', 'May raise all user stats.'),
            (306, 'Tail Glow', 'Bug', 'Status', 20, None, None, False, False, 0, 'Self', 'Sharply raises user Sp. Attack.'),
            (307, 'Rage Powder', 'Bug', 'Status', 20, None, None, False, False, 2, 'UserSide', 'Forces attacks to target user.'),
            (308, 'Sticky Web', 'Bug', 'Status', 20, None, None, False, False, 0, 'Opponents_Field', 'Lowers Speed of switching-in opponents.'),
            (309, 'Defend Order', 'Bug', 'Status', 10, None, None, False, False, 0, 'Self', 'Raises user Defense and Sp. Defense.'),
            (310, 'Heal Order', 'Bug', 'Status', 10, None, None, False, False, 0, 'Self', 'User recovers 50% of max HP.'),

            # NEW POISON MOVES (311-325)
            (311, 'Baneful Bunker', 'Poison', 'Status', 10, None, 100, False, False, 4, 'Self', 'Protects and poisons contact attackers.'),
            (312, 'Shell Side Arm', 'Poison', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Uses Physical or Special depending on which does more damage.'),
            (313, 'Gunk Shot', 'Poison', 'Physical', 5, 120, 80, True, False, 0, 'Normal', 'May poison target.'),
            (314, 'Sludge Wave', 'Poison', 'Special', 10, 95, 100, True, False, 0, 'All_Adjacent', 'May poison adjacent Pokémon.'),
            (315, 'Venoshock', 'Poison', 'Special', 10, 65, 100, True, False, 0, 'Normal', 'Double power if target is poisoned.'),
            (316, 'Cross Poison', 'Poison', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'High critical hit ratio, may poison.'),
            (317, 'Poison Tail', 'Poison', 'Physical', 25, 50, 100, True, True, 0, 'Normal', 'High critical hit ratio, may poison.'),
            (318, 'Clear Smog', 'Poison', 'Special', 15, 50, None, True, False, 0, 'Normal', 'Resets target stat changes.'),
            (319, 'Coil', 'Poison', 'Status', 20, None, None, False, False, 0, 'Self', 'Raises Attack, Defense, and Accuracy.'),
            (320, 'Acid Spray', 'Poison', 'Special', 20, 40, 100, True, False, 0, 'Normal', 'Sharply lowers target Sp. Defense.'),
            (321, 'Acid Armor', 'Poison', 'Status', 20, None, None, False, False, 0, 'Self', 'Sharply raises user Defense.'),
            (322, 'Poison Gas', 'Poison', 'Status', 40, None, 90, False, False, 0, 'All_Adjacent_Foes', 'Poisons adjacent foes.'),
            (323, 'Poison Powder', 'Poison', 'Status', 35, None, 75, False, False, 0, 'Normal', 'Poisons target.'),
            (324, 'Toxic Thread', 'Poison', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Poisons and lowers target Speed.'),
            (325, 'Venom Drench', 'Poison', 'Status', 20, None, 100, False, False, 0, 'All_Adjacent_Foes', 'Lowers stats of poisoned foes.'),

            # NEW GROUND MOVES (326-340)
            (326, 'Precipice Blades', 'Ground', 'Physical', 10, 120, 85, True, False, 0, 'All_Adjacent_Foes', 'Legendary ground blades attack.'),
            (327, 'High Horsepower', 'Ground', 'Physical', 10, 95, 95, True, True, 0, 'Normal', 'A powerful physical attack.'),
            (328, 'Drill Run', 'Ground', 'Physical', 10, 80, 95, True, True, 0, 'Normal', 'High critical hit ratio.'),
            (329, 'Bone Rush', 'Ground', 'Physical', 10, 25, 90, True, False, 0, 'Normal', 'Hits 2-5 times.'),
            (330, 'Mud Bomb', 'Ground', 'Special', 10, 65, 85, True, False, 0, 'Normal', 'May lower target accuracy.'),
            (331, 'Mud Shot', 'Ground', 'Special', 15, 55, 95, True, False, 0, 'Normal', 'Lowers target Speed.'),
            (332, 'Sand Tomb', 'Ground', 'Physical', 15, 35, 85, True, True, 0, 'Normal', 'Traps target for 4-5 turns.'),
            (333, 'Shore Up', 'Ground', 'Status', 10, None, None, False, False, 0, 'Self', 'User recovers 50% HP, 66% in sandstorm.'),
            (334, 'Thousand Arrows', 'Ground', 'Physical', 10, 90, 100, True, False, 0, 'All_Adjacent_Foes', 'Hits Flying types, grounds them.'),
            (335, 'Thousand Waves', 'Ground', 'Physical', 10, 90, 100, True, False, 0, 'All_Adjacent_Foes', 'Prevents target from switching.'),
            (336, 'Land\'s Wrath', 'Ground', 'Physical', 10, 90, 100, True, False, 0, 'All_Adjacent_Foes', 'A powerful ground attack.'),
            (337, 'Rototiller', 'Ground', 'Status', 10, None, None, False, False, 0, 'Field', 'Raises Attack and Sp. Attack of Grass types.'),
            (338, 'Fissure', 'Ground', 'Physical', 5, None, 30, True, False, 0, 'Normal', 'One-hit KO if it hits.'),
            (339, 'Magnitude', 'Ground', 'Physical', 30, None, 100, True, False, 0, 'All_Adjacent', 'Power varies from 10 to 150.'),
            (340, 'Bulldoze', 'Ground', 'Physical', 20, 60, 100, True, False, 0, 'All_Adjacent', 'Lowers target Speed.'),

            # NEW FLYING MOVES (341-355)
            # Removed duplicate Dragon Ascent (341) - already exists as ID 205
            (342, 'Oblivion Wing', 'Flying', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'User recovers 75% of damage dealt.'),
            (343, 'Supersonic Skystrike', 'Flying', 'Physical', 1, None, None, True, False, 0, 'Normal', 'Z-Move. Varies with base move.'),
            (344, 'Acrobatics', 'Flying', 'Physical', 15, 55, 100, True, True, 0, 'Normal', 'Double power if user has no item.'),
            (345, 'Aerial Ace', 'Flying', 'Physical', 20, 60, None, True, True, 0, 'Normal', 'Never misses.'),
            (346, 'Bounce', 'Flying', 'Physical', 5, 85, 85, True, True, 0, 'Normal', 'Bounces turn 1, attacks turn 2, may paralyze.'),
            (347, 'Chatter', 'Flying', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'Confuses target.'),
            (348, 'Defog', 'Flying', 'Status', 15, None, None, False, False, 0, 'Normal', 'Lowers target evasion, clears hazards.'),
            # Removed duplicate Dual Wingbeat (349) - already exists as ID 200
            (350, 'Feather Dance', 'Flying', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Sharply lowers target Attack.'),
            (351, 'Sky Attack', 'Flying', 'Physical', 5, 140, 90, True, False, 0, 'Normal', 'Charges turn 1, attacks turn 2, may cause flinching.'),
            (352, 'Sky Drop', 'Flying', 'Physical', 10, 60, 100, True, True, 0, 'Normal', 'Takes target into air on turn 1, drops on turn 2.'),
            (353, 'Tailwind', 'Flying', 'Status', 15, None, None, False, False, 0, 'UserSide', 'Doubles Speed for 4 turns.'),
            (354, 'Roost', 'Flying', 'Status', 10, None, None, False, False, 0, 'Self', 'User recovers 50% HP, loses Flying type temporarily.'),
            (355, 'Fly', 'Flying', 'Physical', 15, 90, 95, True, True, 0, 'Normal', 'Flies up turn 1, strikes turn 2.'),

            # STATUS & FIELD EFFECT MOVES (356-365)
            (356, 'Court Change', 'Normal', 'Status', 10, None, 100, False, False, 0, 'Field', 'Switches field effects with opponent.'),
            (357, 'Jungle Healing', 'Grass', 'Status', 10, None, 100, False, False, 0, 'UserSide', 'Heals party and cures status.'),
            (358, 'Life Dew', 'Water', 'Status', 10, None, 100, False, False, 0, 'UserSide', 'Heals user and allies by 25%.'),
            # Removed duplicate Meteor Beam (359) - already exists as ID 275
            # Removed duplicate Shell Side Arm (360) - already exists as ID 312
            (361, 'Snap Trap', 'Grass', 'Physical', 15, 35, 100, True, True, 0, 'Normal', 'Traps target for 4-5 turns.'),
            (362, 'Stuff Cheeks', 'Normal', 'Status', 10, None, 100, False, False, 0, 'Self', 'Eats berry, sharply raises Defense.'),
            (363, 'Teatime', 'Normal', 'Status', 10, None, 100, False, False, 0, 'All', 'Forces all Pokémon to eat their berries.'),
            (364, 'Terrain Pulse', 'Normal', 'Special', 10, 50, 100, True, False, 0, 'Normal', 'Type and power change with active terrain.'),
            (365, 'Tri Attack', 'Normal', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'May paralyze, burn, or freeze.'),
        
        ]
        
        # Clear the table first to avoid duplicate errors
        cursor.execute("DELETE FROM moves")
        
        # Insert moves in batches to handle errors
        successful = 0
        problematic_moves = []
        
        for move in moves:
            try:
                cursor.execute('''
                INSERT INTO moves 
                (id, name, type, category, pp, power, accuracy, causes_damage, makes_contact, priority, target_type, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', move)
                successful += 1
            except sqlite3.IntegrityError as e:
                problematic_moves.append((move[0], move[1], str(e)))
                print(f"Failed to insert move {move[0]}: {move[1]} - {e}")
        
        print(f"✅ Successfully inserted {successful} moves")
        if problematic_moves:
            print(f"❌ Failed to insert {len(problematic_moves)} moves")
            for move_id, name, error in problematic_moves:
                print(f"  - {move_id}: {name}")

    def _insert_move_effect_instances(self, cursor):
        """Link ALL moves to their effects"""
        effect_instances = []
        
        # Track missing effects for debugging
        missing_effects = set()
        missing_moves = set()
        
        def add_effect(move_id, effect_name, probability=100, order=1, triggers='OnHit'):
            # Check if move exists
            cursor.execute("SELECT id FROM moves WHERE id = ?", (move_id,))
            if not cursor.fetchone():
                missing_moves.add(move_id)
                return
                
            # Check if effect exists
            effect_id = self._get_effect_id(cursor, effect_name)
            if effect_id:
                effect_instances.append((move_id, effect_id, probability, order, triggers))
            else:
                missing_effects.add(effect_name)
        
        # Clear existing instances first
        cursor.execute("DELETE FROM move_effect_instances")
        
        # Debug: show counts
        cursor.execute("SELECT COUNT(*) FROM moves")
        move_count = cursor.fetchone()[0]
        print(f"Total moves in database: {move_count}")
        
        cursor.execute("SELECT COUNT(*) FROM move_effects") 
        effect_count = cursor.fetchone()[0]
        print(f"Total effects in database: {effect_count}")
        
        # Original moves effects (1-100)
        add_effect(1, 'Burn 10%', 10, 2)
        add_effect(2, 'Burn 10%', 10, 2)
        add_effect(3, 'Burn 10%', 10, 2)
        add_effect(4, 'Burn 10%', 10, 2)
        add_effect(5, 'Recoil 33%', 100, 2)
        add_effect(9, 'Burn 30%', 30, 2)
        add_effect(12, 'Paralysis 10%', 10, 2)
        add_effect(13, 'Paralysis 30%', 30, 2)
        add_effect(14, 'Paralysis 10%', 10, 2)
        add_effect(15, 'Recoil 33%', 100, 2)
        add_effect(19, 'Lower SpDefense 1', 10, 2)
        add_effect(21, 'Priority +1', 100, 1)
        add_effect(22, 'Freeze 10%', 10, 2)
        add_effect(23, 'Freeze 10%', 10, 2)
        add_effect(24, 'Freeze 10%', 10, 2)
        add_effect(26, 'Always Crit', 100, 1)
        add_effect(28, 'Lower Defense 1', 100, 2)
        add_effect(28, 'Lower SpDefense 1', 100, 2)
        add_effect(29, 'Drain 50%', 100, 2)
        add_effect(30, 'Priority +1', 100, 1)
        add_effect(31, 'Poison 30%', 30, 2)
        add_effect(32, 'Poison 30%', 30, 2)
        add_effect(33, 'Poison 30%', 30, 2)
        add_effect(34, 'Poison 30%', 30, 2)
        add_effect(35, 'Poison 100%', 100, 1)
        add_effect(36, 'Lower Accuracy 1', 100, 2)
        add_effect(38, 'Lower SpDefense 1', 10, 2)
        add_effect(40, 'Flinch', 10, 2)
        add_effect(43, 'Recoil 33%', 100, 2)
        add_effect(44, 'Flinch', 30, 2)
        add_effect(45, 'Confusion', 30, 2)
        add_effect(46, 'Confusion', 10, 2)
        add_effect(47, 'Lower SpDefense 1', 10, 2)
        add_effect(48, 'Confusion', 10, 2)
        add_effect(49, 'Flinch', 20, 2)
        add_effect(52, 'Confusion', 10, 2)
        add_effect(54, 'Lower SpDefense 1', 10, 2)
        add_effect(57, 'Flinch', 30, 2)
        add_effect(58, 'Always Crit', 100, 1)
        add_effect(59, 'Raise All Stats 1', 10, 2)
        add_effect(61, 'Paralysis 30%', 30, 2)
        add_effect(62, 'Lower SpDefense 1', 20, 2)
        add_effect(66, 'Paralysis 30%', 30, 2)
        add_effect(70, 'Flinch', 20, 2)
        add_effect(71, 'Flinch', 30, 2)
        add_effect(72, 'Lower Defense 1', 20, 2)
        add_effect(73, 'Flinch', 20, 2)
        add_effect(74, 'Always Crit', 100, 1)
        add_effect(76, 'Raise Attack 1', 10, 2)
        add_effect(77, 'Flinch', 30, 2)
        add_effect(78, 'Lower SpDefense 1', 10, 2)
        add_effect(79, 'Raise Attack 1', 20, 2)
        add_effect(80, 'Priority +1', 100, 1)
        add_effect(83, 'Lower SpAttack 1', 30, 2)
        add_effect(84, 'Lower Attack 1', 10, 2)
        add_effect(85, 'Lower SpAttack 1', 100, 2)
        add_effect(87, 'Flinch', 30, 2)
        add_effect(88, 'Paralysis 30%', 30, 2)
        add_effect(89, 'Recharge Turn', 100, 2)
        add_effect(90, 'Recharge Turn', 100, 2)
        add_effect(91, 'Raise Attack 2', 100, 1)
        add_effect(92, 'Raise SpAttack 1', 100, 1)
        add_effect(92, 'Raise SpDefense 1', 100, 2)
        add_effect(93, 'Paralysis 100%', 100, 1)
        add_effect(94, 'Burn 100%', 100, 1)
        add_effect(95, 'Set Toxic Spikes', 100, 1)
        add_effect(96, 'Set Stealth Rock', 100, 1)
        add_effect(99, 'Heal 50%', 100, 1)
        add_effect(100, 'Force Switch', 100, 1)

        # NEW FIRE MOVES (101-115)
        add_effect(101, 'Burn 20%', 20, 2)
        add_effect(102, 'Burn 50%', 50, 2)
        add_effect(103, 'Burn 100%', 100, 2)
        add_effect(104, 'Burn 10%', 10, 2)
        add_effect(105, 'Lower SpAttack 1', 100, 2)
        add_effect(106, 'Self HP Cost 50%', 100, 2)
        add_effect(107, 'Self HP Cost 50%', 100, 2)
        add_effect(108, 'Change Type Fire Remove', 100, 2)
        add_effect(109, 'Raise Speed 1', 100, 2)
        add_effect(110, 'Item Dependent', 100, 2)
        add_effect(111, 'Lower Defense 1', 100, 2)
        add_effect(112, 'Burn 10%', 10, 2)
        add_effect(113, 'Burn 10%', 10, 2)
        add_effect(113, 'Flinch', 10, 3)
        add_effect(114, 'Recharge Turn', 100, 2)
        add_effect(115, 'Lower SpAttack 2', 100, 2)

        # NEW WATER MOVES (116-130)
        add_effect(116, 'Burn 10%', 10, 2)
        add_effect(117, 'HP Scaling High', 100, 1)
        add_effect(118, 'Speed Dependent', 100, 1)
        add_effect(119, 'Always Crit', 100, 1)
        add_effect(119, 'Ignore Redirection', 100, 1)
        add_effect(120, 'Multi Hit 2', 100, 1)
        add_effect(121, 'Lower Accuracy 1', 50, 2)
        add_effect(122, 'Change Type Water', 100, 1)
        add_effect(124, 'Always Crit', 100, 1)
        add_effect(125, 'Lower Defense 1', 50, 2)
        add_effect(126, 'Flinch', 20, 2)
        add_effect(127, 'Lower Defense 1', 20, 2)
        add_effect(128, 'Lower Speed 1', 10, 2)
        add_effect(129, 'Trap 4-5 Turns', 100, 2)
        add_effect(130, 'HP Scaling High', 100, 1)

        # NEW ELECTRIC MOVES (131-145)
        add_effect(131, 'Paralysis 20%', 20, 2)
        add_effect(132, 'Change Type Normal to Electric', 100, 1)
        add_effect(133, 'Paralysis 100%', 100, 2)
        add_effect(134, 'Terrain Dependent', 100, 1)
        add_effect(135, 'Raise Speed 1', 100, 2)
        add_effect(136, 'Drain 50%', 100, 2)
        add_effect(137, 'Speed Dependent', 100, 1)
        add_effect(138, 'Switch Out', 100, 2)
        add_effect(139, 'Paralysis 30%', 30, 2)
        add_effect(140, 'Recoil 25%', 100, 2)
        add_effect(141, 'Damage Doubling', 100, 1)
        add_effect(142, 'Speed Dependent', 100, 1)
        add_effect(143, 'Flinch', 30, 2)
        add_effect(144, 'Paralysis 100%', 100, 2)
        add_effect(145, 'Raise Defense 1', 100, 1)
        add_effect(145, 'Raise SpDefense 1', 100, 2)

        # NEW GRASS MOVES (146-160)
        add_effect(146, 'Lower SpAttack 2', 100, 2)
        add_effect(147, 'Recoil 25%', 25, 2)
        add_effect(148, 'Drain 50%', 100, 2)
        add_effect(149, 'Change Type Grass', 100, 1)
        add_effect(150, 'Priority +1', 100, 1)
        add_effect(151, 'Always Crit', 100, 1)
        add_effect(152, 'Recoil 33%', 100, 2)
        add_effect(153, 'Lower SpDefense 2', 40, 2)
        add_effect(154, 'Lower SpDefense 1', 100, 2)
        add_effect(155, 'Lower Defense 1', 100, 2)
        add_effect(156, 'Lower Speed 1', 100, 2)
        add_effect(158, 'Flinch', 30, 2)
        add_effect(159, 'Protect', 100, 1)
        add_effect(159, 'Damage Contact', 100, 2)
        add_effect(160, 'Raise Defense 2', 100, 1)

        # NEW PSYCHIC MOVES (161-175)
        add_effect(161, 'Stat Dependent Damage', 100, 1)
        add_effect(162, 'Recharge Turn', 100, 2)
        add_effect(163, 'Lower SpAttack 2', 100, 2)
        add_effect(164, 'Stat Boost Scaling', 100, 1)
        add_effect(165, 'Terrain Dependent', 100, 1)
        add_effect(166, 'Freeze 10%', 10, 2)
        add_effect(167, 'Stat Dependent Damage', 100, 1)
        add_effect(168, 'Type Dependent', 100, 1)
        add_effect(170, 'Flinch', 30, 2)
        add_effect(171, 'Never Miss', 100, 1)
        add_effect(171, 'Ignore Protection', 100, 1)
        add_effect(172, 'Ignore Protection', 100, 1)
        add_effect(172, 'Lower Defense 1', 100, 2)
        add_effect(173, 'Lower SpDefense 1', 50, 2)
        add_effect(174, 'Lower SpAttack 1', 50, 2)
        add_effect(175, 'Speed Swap', 100, 1)

        # NEW DARK MOVES (176-190)
        add_effect(176, 'Always Crit', 100, 1)
        add_effect(177, 'Flinch', 20, 2)
        add_effect(178, 'Never Miss', 100, 1)
        add_effect(179, 'Protect', 100, 1)
        add_effect(179, 'Lower Defense 1', 100, 2)
        add_effect(180, 'Prevent Switching', 100, 2)
        add_effect(181, 'Prevent Sound Moves', 100, 2)
        add_effect(182, 'Ignore Stat Changes', 100, 1)
        add_effect(183, 'Remove Item', 100, 2)
        add_effect(184, 'Pursuit Damage', 100, 1)
        add_effect(185, 'Lower SpAttack 1', 100, 2)
        add_effect(186, 'Use Target Attack', 100, 1)
        add_effect(187, 'Lower Attack 1', 100, 1)
        add_effect(187, 'Lower SpAttack 1', 100, 2)
        add_effect(187, 'Switch Out', 100, 3)
        add_effect(189, 'Raise SpAttack 2', 100, 1)
        add_effect(190, 'Raise Attack 1', 100, 1)
        add_effect(190, 'Raise Accuracy 1', 100, 2)

        # NEW DRAGON MOVES (191-205)
        add_effect(191, 'HP Scaling High', 100, 1)
        add_effect(192, 'Recharge Turn', 100, 2)
        add_effect(193, 'Lower Defense 1', 100, 2)
        add_effect(194, 'Nullify Ability', 100, 2)
        add_effect(195, 'Multi Hit 2', 100, 1)
        add_effect(197, 'Force Switch', 100, 2)
        add_effect(198, 'Lower Attack 1', 100, 2)
        add_effect(199, 'Multi Hit 2-5', 100, 1)
        add_effect(199, 'Raise Speed 1', 100, 2)
        add_effect(199, 'Lower Defense 1', 100, 3)
        add_effect(200, 'Multi Hit 2', 100, 1)
        add_effect(201, 'Raise Attack 1', 100, 1)
        add_effect(201, 'Raise Speed 1', 100, 2)
        add_effect(202, 'Recharge Turn', 100, 2)
        add_effect(203, 'Always Crit', 100, 1)
        add_effect(204, 'Lower SpAttack 2', 100, 2)
        add_effect(205, 'Lower Defense 1', 100, 2)
        add_effect(205, 'Lower SpDefense 1', 100, 2)

        # NEW FAIRY MOVES (206-220)
        add_effect(206, 'Lower SpAttack 2', 100, 2)
        add_effect(207, 'Stat Dependent Damage', 100, 1)
        add_effect(208, 'Confusion', 20, 2)
        add_effect(209, 'Raise Attack 2', 100, 1)
        add_effect(209, 'Raise SpAttack 2', 100, 2)
        add_effect(210, 'Drain 75%', 100, 2)
        add_effect(211, 'Lower Attack 1', 100, 1)
        add_effect(216, 'Priority +1', 100, 1)
        add_effect(216, 'Lower Attack 1', 100, 2)
        add_effect(218, 'Self HP Cost 50%', 100, 2)
        add_effect(219, 'HP Scaling High', 100, 1)
        add_effect(220, 'Confusion', 100, 1)

        # NEW FIGHTING MOVES (221-235)
        add_effect(221, 'Raise All Stats 1', 100, 1)
        add_effect(221, 'Prevent Switching', 100, 2)
        add_effect(222, 'Lower Defense 1', 100, 2)
        add_effect(223, 'Raise Attack 1', 100, 1)
        add_effect(223, 'Raise Defense 1', 100, 2)
        add_effect(223, 'Raise Speed 1', 100, 3)
        add_effect(224, 'Always Crit', 100, 1)
        add_effect(224, 'Lower Defense 1', 30, 2)
        add_effect(224, 'Flinch', 30, 3)
        add_effect(225, 'Never Miss', 100, 1)
        add_effect(226, 'Lower SpDefense 1', 10, 2)
        add_effect(227, 'Priority +1', 100, 1)
        add_effect(228, 'Stat Dependent Damage', 100, 1)
        add_effect(229, 'Multi Hit 3', 100, 1)
        add_effect(229, 'Always Crit', 100, 1)
        add_effect(230, 'Raise Attack 1', 100, 1)
        add_effect(230, 'Raise Defense 1', 100, 2)
        add_effect(231, 'Stat Dependent Damage', 100, 1)
        add_effect(232, 'Speed Dependent', 100, 1)
        add_effect(234, 'Confusion 100%', 100, 2)
        add_effect(235, 'Always Crit', 100, 1)

        # NEW GHOST MOVES (236-250)
        add_effect(236, 'Flinch', 20, 2)
        add_effect(237, 'Item Dependent', 100, 1)
        add_effect(238, 'Prevent Switching', 100, 2)
        add_effect(239, 'Lower Defense 1', 20, 2)
        add_effect(240, 'Ignore Protection', 100, 1)
        add_effect(240, 'Nullify Ability', 100, 1)
        add_effect(241, 'Steal Stat Boosts', 100, 2)
        add_effect(242, 'Change Type Ghost', 100, 1)
        add_effect(244, 'Raise All Stats 1', 10, 2)
        add_effect(249, 'Priority +1', 100, 1)
        add_effect(250, 'HP Scaling High', 100, 1)

        # NEW ICE MOVES (251-265)
        add_effect(251, 'Freeze 10%', 10, 2)
        add_effect(252, 'Multi Hit 3', 100, 1)
        add_effect(255, 'Aurora Veil', 100, 1)
        add_effect(256, 'OHKO', 30, 1)
        add_effect(257, 'Burn 30%', 30, 2)
        add_effect(258, 'Paralysis 30%', 30, 2)
        add_effect(259, 'Always Crit', 100, 1)
        add_effect(260, 'Flinch', 30, 2)
        add_effect(261, 'Multi Hit 2-5', 100, 1)
        add_effect(262, 'Lower Attack 1', 10, 2)
        add_effect(263, 'Mist', 100, 1)
        add_effect(264, 'Haze', 100, 1)
        add_effect(265, 'Freeze 10%', 10, 2)

        # NEW ROCK MOVES (266-280)
        add_effect(266, 'Raise Defense 1', 50, 2)
        add_effect(267, 'Lower Speed 1', 100, 1)
        add_effect(267, 'Change Type Fire Weakness', 100, 2)
        add_effect(268, 'Recharge Turn', 100, 2)
        add_effect(269, 'Recoil 50%', 100, 2)
        add_effect(270, 'Multi Hit 2-5', 100, 1)
        add_effect(271, 'Raise Speed 2', 100, 1)
        add_effect(272, 'Smack Down', 100, 2)
        add_effect(273, 'Wide Guard', 100, 1)
        add_effect(274, 'Priority +1', 100, 1)
        add_effect(275, 'Raise SpAttack 1', 100, 2)

        # NEW STEEL MOVES (281-295)
        add_effect(281, 'Self HP Cost 50%', 100, 2)
        add_effect(282, 'Multi Hit 2', 100, 1)
        add_effect(282, 'Flinch', 30, 2)
        add_effect(283, 'Nullify Ability', 100, 1)
        add_effect(284, 'Nullify Ability', 100, 1)
        add_effect(285, 'Multi Hit 2', 100, 1)
        add_effect(286, 'Prevent Switching', 100, 2)
        add_effect(287, 'Protect', 100, 1)
        add_effect(287, 'Lower Attack 1', 100, 2)
        add_effect(288, 'Never Miss', 100, 1)
        add_effect(291, 'Terrain Dependent', 100, 1)
        add_effect(292, 'Never Miss', 100, 1)
        add_effect(293, 'Lower Accuracy 1', 30, 2)
        add_effect(294, 'Raise Attack 1', 100, 1)
        add_effect(294, 'Raise Speed 2', 100, 2)
        add_effect(295, 'Raise Defense 2', 100, 1)

        # NEW BUG MOVES (296-310)
        add_effect(296, 'Always Crit', 100, 1)
        add_effect(297, 'Lower SpAttack 1', 100, 2)
        add_effect(298, 'Priority +2', 100, 1)
        add_effect(300, 'Lower Attack 1', 100, 2)
        add_effect(301, 'Drain 50%', 100, 2)
        add_effect(302, 'Raise Attack 2', 100, 2)
        add_effect(303, 'Raise SpAttack 1', 100, 1)
        add_effect(303, 'Raise SpDefense 1', 100, 2)
        add_effect(303, 'Raise Speed 1', 100, 3)
        add_effect(304, 'Item Dependent', 100, 2)
        add_effect(305, 'Raise All Stats 1', 10, 2)
        add_effect(306, 'Raise SpAttack 3', 100, 1)
        add_effect(309, 'Raise Defense 1', 100, 1)
        add_effect(309, 'Raise SpDefense 1', 100, 2)
        add_effect(310, 'Heal 50%', 100, 1)

        # NEW POISON MOVES (311-325)
        add_effect(311, 'Protect', 100, 1)
        add_effect(311, 'Poison 100%', 100, 2)
        add_effect(312, 'Stat Dependent Damage', 100, 1)
        add_effect(313, 'Poison 30%', 30, 2)
        add_effect(314, 'Poison 10%', 10, 2)
        add_effect(315, 'HP Scaling High', 100, 1)
        add_effect(316, 'Always Crit', 100, 1)
        add_effect(316, 'Poison 10%', 10, 2)
        add_effect(317, 'Always Crit', 100, 1)
        add_effect(317, 'Poison 10%', 10, 2)
        add_effect(318, 'Clear Stats', 100, 2)
        add_effect(319, 'Raise Attack 1', 100, 1)
        add_effect(319, 'Raise Defense 1', 100, 2)
        add_effect(319, 'Raise Accuracy 1', 100, 3)
        add_effect(320, 'Lower SpDefense 2', 100, 2)
        add_effect(321, 'Raise Defense 2', 100, 1)
        add_effect(322, 'Poison 90%', 90, 1)
        add_effect(323, 'Poison 75%', 75, 1)
        add_effect(324, 'Poison 100%', 100, 1)
        add_effect(324, 'Lower Speed 1', 100, 2)
        add_effect(325, 'Lower Attack 1', 100, 1)
        add_effect(325, 'Lower SpAttack 1', 100, 2)
        add_effect(325, 'Lower Speed 1', 100, 3)

        # NEW GROUND MOVES (326-340)
        add_effect(326, 'Flinch', 10, 2)
        add_effect(329, 'Multi Hit 2-5', 100, 1)
        add_effect(330, 'Lower Accuracy 1', 30, 2)
        add_effect(331, 'Lower Speed 1', 100, 2)
        add_effect(332, 'Trap 4-5 Turns', 100, 2)
        add_effect(333, 'Heal 50%', 100, 1)
        add_effect(338, 'OHKO', 30, 1)
        add_effect(339, 'Variable Power', 100, 1)
        add_effect(340, 'Lower Speed 1', 100, 2)

        # NEW FLYING MOVES (341-355)
        add_effect(341, 'Lower Defense 1', 100, 2)
        add_effect(341, 'Lower SpDefense 1', 100, 2)
        add_effect(342, 'Drain 75%', 100, 2)
        add_effect(344, 'Item Dependent', 100, 1)
        add_effect(345, 'Never Miss', 100, 1)
        add_effect(346, 'Paralysis 30%', 30, 2)
        add_effect(347, 'Confusion 100%', 100, 2)
        add_effect(349, 'Multi Hit 2', 100, 1)
        add_effect(350, 'Lower Attack 2', 100, 1)
        add_effect(351, 'Flinch', 30, 2)
        add_effect(354, 'Heal 50%', 100, 1)

        # STATUS & FIELD EFFECT MOVES (356-365)
        add_effect(356, 'Court Change', 100, 1)
        add_effect(357, 'Heal 25%', 100, 1)
        add_effect(357, 'Cure Status', 100, 2)
        add_effect(358, 'Heal 25%', 100, 1)
        add_effect(359, 'Raise SpAttack 1', 100, 2)
        add_effect(360, 'Stat Dependent Damage', 100, 1)
        add_effect(361, 'Trap 4-5 Turns', 100, 2)
        add_effect(362, 'Raise Defense 2', 100, 1)
        add_effect(363, 'Force Berry', 100, 1)
        add_effect(364, 'Terrain Dependent', 100, 1)
        add_effect(365, 'Paralysis 20%', 20, 2)
        add_effect(365, 'Burn 20%', 20, 3)
        add_effect(365, 'Freeze 20%', 20, 4)

        # Print missing effects for debugging
        if missing_effects:
            print(f"WARNING: Missing effects: {missing_effects}")
            print("These effects will be skipped.")
        
        if missing_moves:
            print(f"WARNING: Missing moves: {missing_moves}")
            print("These moves will be skipped.")
        
        if effect_instances:
            cursor.executemany('''
            INSERT INTO move_effect_instances 
            (move_id, effect_id, probability, effect_order, triggers_on)
            VALUES (?, ?, ?, ?, ?)
            ''', effect_instances)
            print(f"✅ Successfully inserted {len(effect_instances)} move effect instances")
        else:
            print("WARNING: No effect instances to insert!")

    def _get_effect_id(self, cursor, effect_name):
        """Helper to get effect ID by name"""
        cursor.execute("SELECT id FROM move_effects WHERE name = ?", (effect_name,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_move_details(move_id):
    """Get complete move details with effects"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # First get the move basic info
    cursor.execute('SELECT * FROM moves WHERE id = ?', (move_id,))
    move = cursor.fetchone()
    
    if not move:
        conn.close()
        return None
    
    # Then get all effects with their full details
    cursor.execute('''
    SELECT me.name, me.description, me.effect_type, me.status_condition, 
           me.stat_to_change, me.stat_change_amount, me.heal_percentage,
           me.recoil_percentage, me.weather_type, me.field_condition,
           mei.probability, mei.effect_order, mei.triggers_on
    FROM move_effect_instances mei
    JOIN move_effects me ON mei.effect_id = me.id
    WHERE mei.move_id = ?
    ORDER BY mei.effect_order
    ''', (move_id,))
    
    effects = cursor.fetchall()
    conn.close()
    
    # Return move data with effects as a separate list
    return {
        'move': move,
        'effects': effects
    }

def get_all_moves():
    """Get all moves"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM moves ORDER BY name')
    results = cursor.fetchall()
    conn.close()
    return results

def search_moves_by_type(move_type):
    """Search moves by type"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM moves WHERE type = ? ORDER BY name', (move_type,))
    results = cursor.fetchall()
    conn.close()
    return results