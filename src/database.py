import sqlite3
import os
from pathlib import Path

class DatabaseManager:

    def __init__(self, db_path="data/pokemon_battle.db"):
        self.db_path = db_path
        self.ensure_data_directory()

    # *** PUBLIC ***

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
        print("✅ Database structure initialized successfully!")
        print("⚠️  Note: Pokemon, learnsets, and evolutions need to be added separately.")
        print("   Run: pokemon_db = PokemonDataManager(); pokemon_db.initialize_pokemon_data()")

    # *** PRIVATE ***

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
            target_type TEXT CHECK(target_type IN ('Normal', 'Self', 'Adjacent_Ally', 'All_Adjacent', 'All_Adjacent_Foes', 'All', 'Field', 'Opponents_Field', 'UserSide', 'Random_Opponent')) DEFAULT 'Normal',
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
        
        # Create pokemon_learnsets table
        cursor.execute('''
        CREATE TABLE pokemon_learnsets (
            id INTEGER PRIMARY KEY,
            pokemon_id INTEGER NOT NULL,
            move_id INTEGER NOT NULL,
            learn_method TEXT NOT NULL,
            learn_level INTEGER,
            form INTEGER DEFAULT 0,
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(id) ON DELETE CASCADE,
            FOREIGN KEY (move_id) REFERENCES moves(id) ON DELETE CASCADE
        )
        ''')
        
        # Create pokemon_evolutions table
        cursor.execute('''
        CREATE TABLE pokemon_evolutions (
            id INTEGER PRIMARY KEY,
            pokemon_id INTEGER,
            evolves_to_id INTEGER,
            evolution_level INTEGER,
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
            FOREIGN KEY (evolves_to_id) REFERENCES pokemon(id)
        )
        ''')
        
        # Create abilities table
        cursor.execute('''
        CREATE TABLE abilities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            overworld_effect TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create pokemon_abilities junction table
        cursor.execute('''
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
        ''')

    def _get_effect_id(self, cursor, effect_name):
        """Helper to get effect ID by name"""
        cursor.execute("SELECT id FROM move_effects WHERE name = ?", (effect_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    # region Data insertion

    def _insert_move_effect_instances(self, cursor):
        """Link ALL moves to their effects"""
        effect_instances = []

        # Helper to find effect ID by name
        def get_effect_id(name):
            cursor.execute('SELECT id FROM move_effects WHERE name = ?', (name,))
            res = cursor.fetchone()
            return res[0] if res else None

        # Helper to find move ID by name
        def get_move_id(name):
            cursor.execute('SELECT id FROM moves WHERE name = ?', (name,))
            res = cursor.fetchone()
            return res[0] if res else None

        print('Linking move effects...')
        # Move Effects Map
        effects_map = {
            'Absorb': [('Drain 50%', 100, 1, 'OnHit')],
            'Accelerock': [('Priority +1', 100, 1, 'OnHit')],
            'Acid': [('Lower Defense 1', 10, 1, 'OnHit'), ('Lower SpDefense 1', 10, 1, 'OnHit')],
            'Acid Armor': [('Raise Defense 2', 100, 1, 'OnHit')],
            'Acid Spray': [('Lower SpDefense 2', 100, 2, 'OnHit')],
            'Acrobatics': [('Item Dependent', 100, 1, 'OnHit')],
            'Aerial Ace': [('Never Miss', 100, 1, 'OnHit')],
            'Agility': [('Raise Speed 2', 100, 1, 'OnHit')],
            'Air Slash': [('Flinch', 30, 2, 'OnHit')],
            'Amnesia': [('Raise SpDefense 2', 100, 1, 'OnHit')],
            'Anchor Shot': [('Prevent Switching', 100, 2, 'OnHit')],
            'Ancient Power': [('Raise All Stats 1', 10, 2, 'OnHit')],
            'Apple Acid': [('Lower SpDefense 1', 100, 2, 'OnHit')],
            'Aqua Jet': [('Priority +1', 100, 1, 'OnHit')],
            'Aqua Ring': [('Aqua Ring', 100, 1, 'OnHit')],
            'Aromatherapy': [('Cure Status', 100, 1, 'OnHit')],
            'Astral Barrage': [('Flinch', 20, 2, 'OnHit')],
            'Attack Order': [('Always Crit', 100, 1, 'OnHit')],
            'Aura Sphere': [('Never Miss', 100, 1, 'OnHit')],
            'Aura Wheel': [('Raise Speed 1', 100, 2, 'OnHit')],
            'Aurora Beam': [('Lower Attack 1', 10, 2, 'OnHit')],
            'Aurora Veil': [('Aurora Veil', 100, 1, 'OnHit')],
            'Baby-Doll Eyes': [('Priority +1', 100, 1, 'OnHit'), ('Lower Attack 1', 100, 2, 'OnHit')],
            'Baneful Bunker': [('Protect', 100, 1, 'OnHit'), ('Poison 100%', 100, 2, 'OnHit')],
            'Barrage': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Barrier': [('Raise Defense 2', 100, 1, 'OnHit')],
            'Baton Pass': [('Baton Pass', 100, 1, 'OnHit')],
            'Bind': [('Trap 4-5 Turns', 100, 1, 'OnHit')],
            'Bite': [('Flinch', 30, 2, 'OnHit')],
            'Blast Burn': [('Recharge Turn', 100, 2, 'OnHit')],
            'Blizzard': [('Freeze 10%', 10, 2, 'OnHit')],
            'Blue Flare': [('Burn 20%', 20, 2, 'OnHit')],
            'Body Press': [('Stat Dependent Damage', 100, 1, 'OnHit')],
            'Body Slam': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Bolt Beak': [('Speed Dependent', 100, 1, 'OnHit')],
            'Bolt Strike': [('Paralysis 20%', 20, 2, 'OnHit')],
            'Bone Club': [('Flinch', 10, 2, 'OnHit')],
            'Bone Rush': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Bonemerang': [('Multi Hit 2', 100, 1, 'OnHit')],
            'Bounce': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Brave Bird': [('Recoil 33%', 100, 2, 'OnHit')],
            'Breaking Swipe': [('Lower Attack 1', 100, 2, 'OnHit')],
            'Brine': [('HP Scaling High', 100, 1, 'OnHit')],
            'Bubble': [('Lower Speed 1', 10, 1, 'OnHit')],
            'Bubble Beam': [('Lower Speed 1', 10, 2, 'OnHit')],
            'Bug Buzz': [('Lower SpDefense 1', 10, 2, 'OnHit')],
            'Bulk Up': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise Defense 1', 100, 2, 'OnHit')],
            'Bulldoze': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Bullet Punch': [('Priority +1', 100, 1, 'OnHit')],
            'Bullet Seed': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Burn Up': [('Change Type Fire Remove', 100, 2, 'OnHit')],
            'Calm Mind': [('Raise SpAttack 1', 100, 1, 'OnHit'), ('Raise SpDefense 1', 100, 2, 'OnHit')],
            'Chatter': [('Confusion 100%', 100, 2, 'OnHit')],
            'Circle Throw': [('Force Switch', 100, 2, 'OnHit')],
            'Clamp': [('Trap 4-5 Turns', 100, 1, 'OnHit')],
            'Clanging Scales': [('Lower Defense 1', 100, 2, 'OnHit')],
            'Clear Smog': [('Clear Stats', 100, 2, 'OnHit')],
            'Close Combat': [('Lower Defense 1', 100, 2, 'OnHit'), ('Lower SpDefense 1', 100, 2, 'OnHit')],
            'Coaching': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise Defense 1', 100, 2, 'OnHit')],
            'Coil': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise Defense 1', 100, 2, 'OnHit'), ('Raise Accuracy 1', 100, 3, 'OnHit')],
            'Comet Punch': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Confuse Ray': [('Confusion 100%', 100, 1, 'OnHit')],
            'Confusion': [('Confusion', 10, 2, 'OnHit')],
            'Constrict': [('Lower Speed 1', 10, 1, 'OnHit')],
            'Core Enforcer': [('Nullify Ability', 100, 2, 'OnHit')],
            'Cotton Guard': [('Raise Defense 2', 100, 1, 'OnHit')],
            'Court Change': [('Court Change', 100, 1, 'OnHit')],
            'Crabhammer': [('Always Crit', 100, 1, 'OnHit')],
            'Cross Chop': [('Always Crit', 100, 1, 'OnHit')],
            'Cross Poison': [('Always Crit', 100, 1, 'OnHit'), ('Poison 10%', 10, 2, 'OnHit')],
            'Crunch': [('Lower Defense 1', 20, 2, 'OnHit')],
            'Dark Pulse': [('Flinch', 20, 2, 'OnHit')],
            'Darkest Lariat': [('Ignore Stat Changes', 100, 1, 'OnHit')],
            'Decorate': [('Raise Attack 2', 100, 1, 'OnHit'), ('Raise SpAttack 2', 100, 2, 'OnHit')],
            'Defend Order': [('Raise Defense 1', 100, 1, 'OnHit'), ('Raise SpDefense 1', 100, 2, 'OnHit')],
            'Defense Curl': [('Raise Defense 1', 100, 1, 'OnHit')],
            'Detect': [('Protect', 100, 1, 'OnHit')],
            'Diamond Storm': [('Raise Defense 1', 50, 2, 'OnHit')],
            'Disable': [('Disable', 100, 1, 'OnHit')],
            'Discharge': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Dizzy Punch': [('Confusion 10%', 10, 1, 'OnHit')],
            'Double Iron Bash': [('Multi Hit 2', 100, 1, 'OnHit'), ('Flinch', 30, 2, 'OnHit')],
            'Double Kick': [('Multi Hit 2', 100, 1, 'OnHit')],
            'Double Slap': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Double Team': [('Raise Evasion 1', 100, 1, 'OnHit')],
            'Double-Edge': [('Recoil 25%', 100, 1, 'OnHit')],
            'Draco Meteor': [('Lower SpAttack 2', 100, 2, 'OnHit')],
            'Dragon Ascent': [('Lower Defense 1', 100, 2, 'OnHit'), ('Lower SpDefense 1', 100, 2, 'OnHit')],
            'Dragon Breath': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Dragon Dance': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise Speed 1', 100, 2, 'OnHit')],
            'Dragon Darts': [('Multi Hit 2', 100, 1, 'OnHit')],
            'Dragon Energy': [('HP Scaling High', 100, 1, 'OnHit')],
            'Dragon Rush': [('Flinch', 20, 2, 'OnHit')],
            'Dragon Tail': [('Force Switch', 100, 2, 'OnHit')],
            'Drain Punch': [('Drain 50%', 100, 2, 'OnHit')],
            'Draining Kiss': [('Drain 75%', 100, 2, 'OnHit')],
            'Dream Eater': [('Drain 50%', 100, 2, 'OnHit')],
            'Drum Beating': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Dual Chop': [('Multi Hit 2', 100, 1, 'OnHit')],
            'Dual Wingbeat': [('Multi Hit 2', 100, 1, 'OnHit')],
            'Dynamic Punch': [('Confusion 100%', 100, 2, 'OnHit')],
            'Earth Power': [('Lower SpDefense 1', 10, 2, 'OnHit')],
            'Electric Terrain': [('Electric Terrain', 100, 1, 'OnHit')],
            'Electro Ball': [('Speed Dependent', 100, 1, 'OnHit')],
            'Ember': [('Burn 10%', 10, 2, 'OnHit')],
            'Encore': [('Encore', 100, 1, 'OnHit')],
            'Energy Ball': [('Lower SpDefense 1', 10, 2, 'OnHit')],
            'Eternabeam': [('Recharge Turn', 100, 2, 'OnHit')],
            'Expanding Force': [('Terrain Dependent', 100, 1, 'OnHit')],
            'Extreme Speed': [('Priority +1', 100, 1, 'OnHit')],
            'Fake Out': [('Flinch', 100, 1, 'OnHit')],
            'False Surrender': [('Never Miss', 100, 1, 'OnHit')],
            'Feather Dance': [('Lower Attack 2', 100, 1, 'OnHit')],
            'Feint': [('Ignore Protection', 100, 1, 'OnHit'), ('Priority +1', 100, 2, 'OnHit')],
            'Fell Stinger': [('Raise Attack 2', 100, 2, 'OnHit')],
            'Fiery Wrath': [('Flinch', 20, 2, 'OnHit')],
            'Fire Blast': [('Burn 10%', 10, 2, 'OnHit')],
            'Fire Fang': [('Burn 10%', 10, 2, 'OnHit'), ('Flinch', 10, 3, 'OnHit')],
            'Fire Lash': [('Lower Defense 1', 100, 2, 'OnHit')],
            'Fire Punch': [('Burn 10%', 10, 2, 'OnHit')],
            'Fire Spin': [('Trap 4-5 Turns', 100, 1, 'OnHit')],
            'First Impression': [('Priority +2', 100, 1, 'OnHit')],
            'Fishious Rend': [('Speed Dependent', 100, 1, 'OnHit')],
            'Fissure': [('OHKO', 30, 1, 'OnHit')],
            'Flame Charge': [('Raise Speed 1', 100, 2, 'OnHit')],
            'Flamethrower': [('Burn 10%', 10, 2, 'OnHit')],
            'Flare Blitz': [('Recoil 33%', 100, 2, 'OnHit')],
            'Flash': [('Lower Accuracy 1', 100, 1, 'OnHit')],
            'Flash Cannon': [('Lower SpDefense 1', 10, 2, 'OnHit')],
            'Fleur Cannon': [('Lower SpAttack 2', 100, 2, 'OnHit')],
            'Flip Turn': [('Switch Out', 100, 2, 'OnHit')],
            'Focus Blast': [('Lower SpDefense 1', 10, 2, 'OnHit')],
            'Forests Curse': [('Change Type Grass', 100, 1, 'OnHit')],
            'Foul Play': [('Use Target Attack', 100, 1, 'OnHit')],
            'Freeze Shock': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Freezing Glare': [('Freeze 10%', 10, 2, 'OnHit')],
            'Frost Breath': [('Always Crit', 100, 1, 'OnHit')],
            'Fury Attack': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Fury Swipes': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Fusion Bolt': [('Damage Doubling', 100, 1, 'OnHit')],
            'Gear Grind': [('Multi Hit 2', 100, 1, 'OnHit')],
            'Giga Impact': [('Recharge Turn', 100, 2, 'OnHit')],
            'Glacial Lance': [('Freeze 10%', 10, 2, 'OnHit')],
            'Glare': [('Paralysis 100%', 100, 1, 'OnHit')],
            'Grassy Glide': [('Priority +1', 100, 1, 'OnHit')],
            'Grassy Terrain': [('Grassy Terrain', 100, 1, 'OnHit')],
            'Grav Apple': [('Lower Defense 1', 100, 2, 'OnHit')],
            'Growl': [('Lower Attack 1', 100, 1, 'OnHit')],
            'Growth': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise SpAttack 1', 100, 1, 'OnHit')],
            'Guillotine': [('OHKO', 30, 1, 'OnHit')],
            'Gunk Shot': [('Poison 30%', 30, 2, 'OnHit')],
            'Hail': [('Set Hail', 100, 1, 'OnHit')],
            'Harden': [('Raise Defense 1', 100, 1, 'OnHit')],
            'Haze': [('Haze', 100, 1, 'OnHit')],
            'Head Smash': [('Recoil 50%', 100, 2, 'OnHit')],
            'Headbutt': [('Flinch', 30, 2, 'OnHit')],
            'Heal Bell': [('Cure Status', 100, 1, 'OnHit')],
            'Heal Order': [('Heal 50%', 100, 1, 'OnHit')],
            'Heart Stamp': [('Flinch', 30, 2, 'OnHit')],
            'Heat Wave': [('Burn 10%', 10, 2, 'OnHit')],
            'Hone Claws': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise Accuracy 1', 100, 2, 'OnHit')],
            'Horn Drill': [('OHKO', 30, 1, 'OnHit')],
            'Horn Leech': [('Drain 50%', 100, 2, 'OnHit')],
            'Hurricane': [('Confusion', 30, 2, 'OnHit')],
            'Hyper Beam': [('Recharge Turn', 100, 2, 'OnHit')],
            'Hyper Fang': [('Flinch 30%', 30, 1, 'OnHit')],
            'Hyperspace Fury': [('Ignore Protection', 100, 1, 'OnHit'), ('Lower Defense 1', 100, 2, 'OnHit')],
            'Hyperspace Hole': [('Never Miss', 100, 1, 'OnHit'), ('Ignore Protection', 100, 1, 'OnHit')],
            'Hypnosis': [('Sleep', 100, 1, 'OnHit')],
            'Ice Beam': [('Freeze 10%', 10, 2, 'OnHit')],
            'Ice Burn': [('Burn 30%', 30, 2, 'OnHit')],
            'Ice Punch': [('Freeze 10%', 10, 2, 'OnHit')],
            'Ice Shard': [('Priority +1', 100, 1, 'OnHit')],
            'Icicle Crash': [('Flinch', 30, 2, 'OnHit')],
            'Icicle Spear': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Incinerate': [('Item Dependent', 100, 2, 'OnHit')],
            'Infernal Parade': [('HP Scaling High', 100, 1, 'OnHit')],
            'Inferno': [('Burn 100%', 100, 2, 'OnHit')],
            'Ingrain': [('Ingrain', 100, 1, 'OnHit')],
            'Iron Defense': [('Raise Defense 2', 100, 1, 'OnHit')],
            'Iron Head': [('Flinch', 30, 2, 'OnHit')],
            'Jaw Lock': [('Prevent Switching', 100, 2, 'OnHit')],
            'Jungle Healing': [('Heal 25%', 100, 1, 'OnHit'), ('Cure Status', 100, 2, 'OnHit')],
            'Karate Chop': [('Always Crit', 100, 1, 'OnHit')],
            'Kinesis': [('Lower Accuracy 1', 100, 1, 'OnHit')],
            'Kings Shield': [('Protect', 100, 1, 'OnHit'), ('Lower Attack 1', 100, 2, 'OnHit')],
            'Knock Off': [('Remove Item', 100, 2, 'OnHit')],
            'Leaf Blade': [('Always Crit', 100, 1, 'OnHit')],
            'Leaf Storm': [('Lower SpAttack 2', 100, 2, 'OnHit')],
            'Leech Life': [('Drain 50%', 100, 2, 'OnHit')],
            'Leech Seed': [('Trap 4-5 Turns', 100, 1, 'OnHit')],
            'Leer': [('Lower Defense 1', 100, 1, 'OnHit')],
            'Lick': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Life Dew': [('Heal 25%', 100, 1, 'OnHit')],
            'Light That Burns The Sky': [('Stat Dependent Damage', 100, 1, 'OnHit')],
            'Liquidation': [('Lower Defense 1', 20, 2, 'OnHit')],
            'Lovely Kiss': [('Sleep 100%', 100, 1, 'OnHit')],
            'Lunge': [('Lower Attack 1', 100, 2, 'OnHit')],
            'Luster Purge': [('Lower SpDefense 1', 50, 2, 'OnHit')],
            'Mach Punch': [('Priority +1', 100, 1, 'OnHit')],
            'Magic Coat': [('Remove Hazards', 100, 1, 'OnHit'), ('Lower Accuracy 1', 100, 2, 'OnHit')],
            'Magnet Bomb': [('Never Miss', 100, 1, 'OnHit')],
            'Magnetic Flux': [('Raise Defense 1', 100, 1, 'OnHit'), ('Raise SpDefense 1', 100, 2, 'OnHit')],
            'Magnitude': [('Variable Power', 100, 1, 'OnHit')],
            'Meditate': [('Raise Attack 1', 100, 1, 'OnHit')],
            'Mega Drain': [('Drain 50%', 100, 1, 'OnHit')],
            'Metal Claw': [('Raise Attack 1', 10, 2, 'OnHit')],
            'Meteor Beam': [('Raise SpAttack 1', 100, 2, 'OnHit')],
            'Meteor Mash': [('Raise Attack 1', 20, 2, 'OnHit')],
            'Milk Drink': [('Heal 50%', 100, 1, 'OnHit')],
            'Mind Blown': [('Self HP Cost 50%', 100, 2, 'OnHit')],
            'Minimize': [('Raise Evasion 2', 100, 1, 'OnHit')],
            'Mirror Shot': [('Lower Accuracy 1', 30, 2, 'OnHit')],
            'Mist': [('Mist', 100, 1, 'OnHit')],
            'Mist Ball': [('Lower SpAttack 1', 50, 2, 'OnHit')],
            'Misty Explosion': [('Self HP Cost 50%', 100, 2, 'OnHit')],
            'Misty Terrain': [('Misty Terrain', 100, 1, 'OnHit')],
            'Moonblast': [('Lower SpAttack 1', 30, 2, 'OnHit')],
            'Moongeist Beam': [('Ignore Protection', 100, 1, 'OnHit'), ('Nullify Ability', 100, 1, 'OnHit')],
            'Moonlight': [('Heal 50%', 100, 1, 'OnHit')],
            'Morning Sun': [('Heal 50%', 100, 1, 'OnHit')],
            'Mud Bomb': [('Lower Accuracy 1', 30, 2, 'OnHit')],
            'Mud Shot': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Mud Slap': [('Lower Accuracy 1', 100, 2, 'OnHit')],
            'Mystical Fire': [('Lower SpAttack 1', 100, 2, 'OnHit')],
            'Nasty Plot': [('Raise SpAttack 2', 100, 1, 'OnHit')],
            'Nature Madness': [('HP Scaling High', 100, 1, 'OnHit')],
            'Needle Arm': [('Flinch', 30, 2, 'OnHit')],
            'Night Slash': [('Always Crit', 100, 1, 'OnHit')],
            'No Retreat': [('Raise All Stats 1', 100, 1, 'OnHit'), ('Prevent Switching', 100, 2, 'OnHit')],
            'Nuzzle': [('Paralysis 100%', 100, 2, 'OnHit')],
            'Oblivion Wing': [('Drain 75%', 100, 2, 'OnHit')],
            'Obstruct': [('Protect', 100, 1, 'OnHit'), ('Lower Defense 1', 100, 2, 'OnHit')],
            'Octazooka': [('Lower Accuracy 1', 50, 2, 'OnHit')],
            'Ominous Wind': [('Raise All Stats 1', 10, 2, 'OnHit')],
            'Origin Pulse': [('Burn 10%', 10, 2, 'OnHit')],
            'Overheat': [('Lower SpAttack 2', 100, 2, 'OnHit')],
            'Parabolic Charge': [('Drain 50%', 100, 2, 'OnHit')],
            'Parting Shot': [('Lower Attack 1', 100, 1, 'OnHit'), ('Lower SpAttack 1', 100, 2, 'OnHit'), ('Switch Out', 100, 3, 'OnHit')],
            'Petal Dance': [('Confusion 10%', 10, 1, 'OnHit')],
            'Photon Geyser': [('Stat Dependent Damage', 100, 1, 'OnHit')],
            'Pin Missile': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Plasma Fists': [('Change Type Normal to Electric', 100, 1, 'OnHit')],
            'Play Nice': [('Lower Attack 1', 100, 1, 'OnHit')],
            'Play Rough': [('Lower Attack 1', 10, 2, 'OnHit')],
            'Poison Gas': [('Poison 90%', 90, 1, 'OnHit')],
            'Poison Jab': [('Poison 30%', 30, 2, 'OnHit')],
            'Poison Powder': [('Poison 75%', 75, 1, 'OnHit')],
            'Poison Sting': [('Poison 30%', 30, 2, 'OnHit')],
            'Poison Tail': [('Always Crit', 100, 1, 'OnHit'), ('Poison 10%', 10, 2, 'OnHit')],
            'Poltergeist': [('Item Dependent', 100, 1, 'OnHit')],
            'Powder Snow': [('Freeze 10%', 10, 2, 'OnHit')],
            'Power Whip': [('Recoil 25%', 25, 2, 'OnHit')],
            'Precipice Blades': [('Flinch', 10, 2, 'OnHit')],
            'Prismatic Laser': [('Recharge Turn', 100, 2, 'OnHit')],
            'Protect': [('Protect', 100, 1, 'OnHit')],
            'Psybeam': [('Confusion', 10, 2, 'OnHit')],
            'Psych Up': [('Copy Stat Stages', 100, 1, 'OnHit')],
            'Psychic': [('Lower SpDefense 1', 10, 2, 'OnHit')],
            'Psychic Terrain': [('Psychic Terrain', 100, 1, 'OnHit')],
            'Psycho Boost': [('Lower SpAttack 2', 100, 2, 'OnHit')],
            'Psystrike': [('Stat Dependent Damage', 100, 1, 'OnHit')],
            'Pursuit': [('Pursuit Damage', 100, 1, 'OnHit')],
            'Pyro Ball': [('Burn 10%', 10, 2, 'OnHit')],
            'Quick Attack': [('Priority +1', 100, 1, 'OnHit')],
            'Quiver Dance': [('Raise SpAttack 1', 100, 1, 'OnHit'), ('Raise SpDefense 1', 100, 2, 'OnHit'), ('Raise Speed 1', 100, 3, 'OnHit')],
            'Rage': [('Raise Attack 1', 10, 1, 'OnHit')],
            'Rain Dance': [('Set Rain', 100, 1, 'OnHit')],
            'Rapid Spin': [('Remove Hazards', 100, 1, 'OnHit'), ('Raise Speed 1', 100, 2, 'OnHit')],
            'Razor Leaf': [('High Crit 1', 100, 1, 'OnHit')],
            'Razor Shell': [('Lower Defense 1', 50, 2, 'OnHit')],
            'Recover': [('Heal 50%', 100, 1, 'OnHit')],
            'Rest': [('Sleep', 100, 1, 'OnHit'), ('Heal 50%', 100, 2, 'OnHit')],
            'Revenge': [('Speed Dependent', 100, 1, 'OnHit')],
            'Rising Voltage': [('Terrain Dependent', 100, 1, 'OnHit')],
            'Roar': [('Force Switch', 100, 1, 'OnHit')],
            'Roar of Time': [('Recharge Turn', 100, 2, 'OnHit')],
            'Rock Blast': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Rock Polish': [('Raise Speed 2', 100, 1, 'OnHit')],
            'Rock Slide': [('Flinch', 30, 2, 'OnHit')],
            'Rock Wrecker': [('Recharge Turn', 100, 2, 'OnHit')],
            'Rolling Kick': [('Flinch 30%', 30, 1, 'OnHit')],
            'Roost': [('Heal 50%', 100, 1, 'OnHit')],
            'Sacred Fire': [('Burn 50%', 50, 2, 'OnHit')],
            'Safeguard': [('Safeguard', 100, 1, 'OnHit')],
            'Sand Attack': [('Lower Accuracy 1', 100, 1, 'OnHit')],
            'Sand Tomb': [('Trap 4-5 Turns', 100, 2, 'OnHit')],
            'Sandstorm': [('Set Sandstorm', 100, 1, 'OnHit')],
            'Scald': [('Burn 30%', 30, 2, 'OnHit')],
            'Scale Shot': [('Multi Hit 2-5', 100, 1, 'OnHit'), ('Raise Speed 1', 100, 2, 'OnHit'), ('Lower Defense 1', 100, 3, 'OnHit')],
            'Screech': [('Lower Defense 2', 100, 1, 'OnHit')],
            'Secret Sword': [('Stat Dependent Damage', 100, 1, 'OnHit')],
            'Seed Flare': [('Lower SpDefense 2', 40, 2, 'OnHit')],
            'Shadow Ball': [('Lower SpDefense 1', 20, 2, 'OnHit')],
            'Shadow Bone': [('Lower Defense 1', 20, 2, 'OnHit')],
            'Shadow Sneak': [('Priority +1', 100, 1, 'OnHit')],
            'Sharpen': [('Raise Attack 1', 100, 1, 'OnHit')],
            'Sheer Cold': [('OHKO', 30, 1, 'OnHit')],
            'Shell Side Arm': [('Stat Dependent Damage', 100, 1, 'OnHit')],
            'Shell Smash': [('Raise Attack 2', 100, 1, 'OnHit'), ('Raise SpAttack 2', 100, 2, 'OnHit'), ('Raise Speed 2', 100, 3, 'OnHit'), ('Lower Defense 1', 100, 4, 'OnHit'), ('Lower SpDefense 1', 100, 5, 'OnHit')],
            'Shell Trap': [('Self HP Cost 50%', 100, 2, 'OnHit')],
            'Shift Gear': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise Speed 2', 100, 2, 'OnHit')],
            'Shore Up': [('Heal 50%', 100, 1, 'OnHit')],
            'Signal Beam': [('Confusion', 10, 2, 'OnHit')],
            'Silver Wind': [('Raise All Stats 1', 10, 2, 'OnHit')],
            'Sing': [('Sleep 100%', 100, 1, 'OnHit')],
            'Skitter Smack': [('Lower SpAttack 1', 100, 2, 'OnHit')],
            'Skull Bash': [('Raise Attack 1', 10, 1, 'OnHit'), ('Raise Defense 1', 10, 1, 'OnHit')],
            'Sky Attack': [('Flinch', 30, 2, 'OnHit')],
            'Slack Off': [('Heal 50%', 100, 1, 'OnHit')],
            'Slash': [('High Crit 1', 100, 1, 'OnHit')],
            'Sleep Powder': [('Sleep', 100, 1, 'OnHit')],
            'Sludge': [('Poison 30%', 30, 2, 'OnHit')],
            'Sludge Bomb': [('Poison 30%', 30, 2, 'OnHit')],
            'Sludge Wave': [('Poison 10%', 10, 2, 'OnHit')],
            'Smack Down': [('Smack Down', 100, 2, 'OnHit')],
            'Smart Strike': [('Never Miss', 100, 1, 'OnHit')],
            'Smog': [('Poison 30%', 30, 1, 'OnHit')],
            'Smokescreen': [('Lower Accuracy 1', 100, 1, 'OnHit')],
            'Snap Trap': [('Trap 4-5 Turns', 100, 2, 'OnHit')],
            'Snarl': [('Lower SpAttack 1', 100, 2, 'OnHit')],
            'Snipe Shot': [('Always Crit', 100, 1, 'OnHit'), ('Ignore Redirection', 100, 1, 'OnHit')],
            'Soak': [('Change Type Water', 100, 1, 'OnHit')],
            'Soft-Boiled': [('Heal 50%', 100, 1, 'OnHit')],
            'Spacial Rend': [('Always Crit', 100, 1, 'OnHit')],
            'Spectral Thief': [('Steal Stat Boosts', 100, 2, 'OnHit')],
            'Speed Swap': [('Speed Swap', 100, 1, 'OnHit')],
            'Spike Cannon': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Spikes': [('Set Spikes', 100, 1, 'OnHit')],
            'Spiky Shield': [('Protect', 100, 1, 'OnHit'), ('Damage Contact', 100, 2, 'OnHit')],
            'Spirit Break': [('Lower SpAttack 1', 100, 2, 'OnHit')],
            'Spirit Shackle': [('Prevent Switching', 100, 2, 'OnHit')],
            'Spore': [('Sleep', 100, 1, 'OnHit')],
            'Stealth Rock': [('Set Stealth Rock', 100, 1, 'OnHit')],
            'Steel Beam': [('Self HP Cost 50%', 100, 2, 'OnHit')],
            'Steel Roller': [('Terrain Dependent', 100, 1, 'OnHit')],
            'Stomp': [('Flinch 30%', 30, 1, 'OnHit')],
            'Stone Edge': [('Always Crit', 100, 1, 'OnHit')],
            'Stored Power': [('Stat Boost Scaling', 100, 1, 'OnHit')],
            'Strange Steam': [('Confusion', 20, 2, 'OnHit')],
            'String Shot': [('Lower Speed 2', 100, 1, 'OnHit')],
            'Stuff Cheeks': [('Raise Defense 2', 100, 1, 'OnHit')],
            'Stun Spore': [('Paralysis 100%', 100, 1, 'OnHit')],
            'Submission': [('Recoil 25%', 100, 1, 'OnHit')],
            'Substitute': [('Create Substitute', 100, 1, 'OnHit')],
            'Sunny Day': [('Set Sun', 100, 1, 'OnHit')],
            'Sunsteel Strike': [('Nullify Ability', 100, 1, 'OnHit')],
            'Supersonic': [('Confusion 100%', 100, 1, 'OnHit')],
            'Surging Strikes': [('Multi Hit 3', 100, 1, 'OnHit'), ('Always Crit', 100, 1, 'OnHit')],
            'Sweet Kiss': [('Confusion', 100, 1, 'OnHit')],
            'Switcheroo': [('Swap Items', 100, 1, 'OnHit')],
            'Swords Dance': [('Raise Attack 2', 100, 1, 'OnHit')],
            'Synchronoise': [('Type Dependent', 100, 1, 'OnHit')],
            'Synthesis': [('Heal 50%', 100, 1, 'OnHit')],
            'Tail Glow': [('Raise SpAttack 3', 100, 1, 'OnHit')],
            'Tail Slap': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Tail Whip': [('Lower Defense 1', 100, 1, 'OnHit')],
            'Take Down': [('Recoil 25%', 100, 1, 'OnHit')],
            'Tar Shot': [('Lower Speed 1', 100, 1, 'OnHit'), ('Change Type Fire Weakness', 100, 2, 'OnHit')],
            'Teatime': [('Force Berry', 100, 1, 'OnHit')],
            'Teleport': [('Switch Out', 100, 1, 'OnHit')],
            'Terrain Pulse': [('Terrain Dependent', 100, 1, 'OnHit')],
            'Thrash': [('Confusion 10%', 10, 1, 'OnHit')],
            'Throat Chop': [('Prevent Sound Moves', 100, 2, 'OnHit')],
            'Thunder': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Thunder Punch': [('Paralysis 10%', 10, 2, 'OnHit')],
            'Thunder Shock': [('Paralysis 10%', 10, 1, 'OnHit')],
            'Thunder Wave': [('Paralysis 100%', 100, 1, 'OnHit')],
            'Thunderbolt': [('Paralysis 10%', 10, 2, 'OnHit')],
            'Thunderous Kick': [('Lower Defense 1', 100, 2, 'OnHit')],
            'Torment': [('Torment', 100, 1, 'OnHit')],
            'Toxic': [('Poison 100%', 100, 1, 'OnHit')],
            'Toxic Spikes': [('Set Toxic Spikes', 100, 1, 'OnHit')],
            'Toxic Thread': [('Poison 100%', 100, 1, 'OnHit'), ('Lower Speed 1', 100, 2, 'OnHit')],
            'Tri Attack': [('Paralysis 20%', 20, 2, 'OnHit'), ('Burn 20%', 20, 3, 'OnHit'), ('Freeze 20%', 20, 4, 'OnHit')],
            'Trick': [('Swap Items', 100, 1, 'OnHit')],
            'Trick Room': [('Trick Room', 100, 1, 'OnHit')],
            'Trick-or-Treat': [('Change Type Ghost', 100, 1, 'OnHit')],
            'Triple Arrows': [('Always Crit', 100, 1, 'OnHit'), ('Lower Defense 1', 30, 2, 'OnHit'), ('Flinch', 30, 3, 'OnHit')],
            'Triple Axel': [('Multi Hit 3', 100, 1, 'OnHit')],
            'Twineedle': [('Multi Hit 2', 100, 1, 'OnHit'), ('Poison 20%', 20, 2, 'OnHit')],
            'Vacuum Wave': [('Priority +1', 100, 1, 'OnHit')],
            'Venom Drench': [('Lower Attack 1', 100, 1, 'OnHit'), ('Lower SpAttack 1', 100, 2, 'OnHit'), ('Lower Speed 1', 100, 3, 'OnHit')],
            'Venoshock': [('HP Scaling High', 100, 1, 'OnHit')],
            'Victory Dance': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise Defense 1', 100, 2, 'OnHit'), ('Raise Speed 1', 100, 3, 'OnHit')],
            'Volt Switch': [('Switch Out', 100, 2, 'OnHit')],
            'Volt Tackle': [('Recoil 33%', 100, 2, 'OnHit')],
            'Water Shuriken': [('Multi Hit 2-5', 100, 1, 'OnHit'), ('Priority +1', 100, 2, 'OnHit')],
            'Water Spout': [('HP Scaling High', 100, 1, 'OnHit')],
            'Waterfall': [('Flinch', 20, 2, 'OnHit')],
            'Weather Ball': [('Terrain Dependent', 100, 1, 'OnHit')],
            'Whirlpool': [('Trap 4-5 Turns', 100, 2, 'OnHit')],
            'Whirlwind': [('Force Switch', 100, 1, 'OnHit')],
            'Wicked Blow': [('Always Crit', 100, 1, 'OnHit')],
            'Wide Guard': [('Wide Guard', 100, 1, 'OnHit')],
            'Wild Charge': [('Recoil 25%', 100, 2, 'OnHit')],
            'Will-O-Wisp': [('Burn 100%', 100, 1, 'OnHit')],
            'Wish': [('Wish', 100, 1, 'OnHit')],
            'Withdraw': [('Raise Defense 1', 100, 1, 'OnHit')],
            'Wood Hammer': [('Recoil 33%', 100, 2, 'OnHit')],
            'Wrap': [('Trap 4-5 Turns', 100, 1, 'OnHit')],
            'Yawn': [('Yawn', 100, 1, 'OnHit')],
            'Zap Cannon': [('Paralysis 100%', 100, 2, 'OnHit')],
            'Zen Headbutt': [('Flinch', 20, 2, 'OnHit')],
            'Zing Zap': [('Flinch', 30, 2, 'OnHit')],
            # Complex Moves - Charge/Invulnerability/Special Mechanics
            'Solar Beam': [('Charge Turn', 100, 1, 'OnHit')],
            'Sky Attack': [('Charge Turn', 100, 1, 'OnHit'), ('Flinch', 30, 2, 'OnHit')],
            'Razor Wind': [('Charge Turn', 100, 1, 'OnHit')],
            'Skull Bash': [('Charge Turn', 100, 1, 'OnHit'), ('Raise Defense 1', 100, 2, 'OnHit')],
            'Geomancy': [('Charge Turn', 100, 1, 'OnHit'), ('Raise SpAttack 2', 100, 2, 'OnHit'), ('Raise SpDefense 2', 100, 3, 'OnHit'), ('Raise Speed 2', 100, 4, 'OnHit')],
            'Freeze Shock': [('Charge Turn', 100, 1, 'OnHit'), ('Paralysis 30%', 30, 2, 'OnHit')],
            'Ice Burn': [('Charge Turn', 100, 1, 'OnHit'), ('Burn 30%', 30, 2, 'OnHit')],
            'Meteor Beam': [('Charge Turn', 100, 1, 'OnHit'), ('Raise SpAttack 1', 100, 2, 'OnHit')],
            'Dig': [('Dig', 100, 1, 'OnHit')],
            'Fly': [('Fly', 100, 1, 'OnHit')],
            'Bounce': [('Fly', 100, 1, 'OnHit'), ('Paralysis 30%', 30, 2, 'OnHit')],
            'Dive': [('Dive', 100, 1, 'OnHit')],
            'Phantom Force': [('Shadow Force', 100, 1, 'OnHit')],
            'Shadow Force': [('Shadow Force', 100, 1, 'OnHit')],
            'Seismic Toss': [('Fixed Damage Level', 100, 1, 'OnHit')],
            'Night Shade': [('Fixed Damage Level', 100, 1, 'OnHit')],
            'Super Fang': [('Fixed Damage 50% HP', 100, 1, 'OnHit')],
            'Psywave': [('Fixed Damage Random', 100, 1, 'OnHit')],
            'Sonic Boom': [('Fixed Damage 20', 100, 1, 'OnHit')],
            'Dragon Rage': [('Fixed Damage 40', 100, 1, 'OnHit')],
            'Low Kick': [('Weight Damage', 100, 1, 'OnHit')],
            'Grass Knot': [('Weight Damage', 100, 1, 'OnHit')],
            'Counter': [('Counter', 100, 1, 'OnHit')],
            'Mirror Coat': [('Mirror Coat', 100, 1, 'OnHit')],
            'Metal Burst': [('Metal Burst', 100, 1, 'OnHit')],
            'Bide': [('Bide', 100, 1, 'OnHit')],
            'Endeavor': [('Endeavor', 100, 1, 'OnHit')],
            'Final Gambit': [('Final Gambit', 100, 1, 'OnHit')],
            'Mirror Move': [('Mirror Move', 100, 1, 'OnHit')],
            'Metronome': [('Metronome', 100, 1, 'OnHit')],
            'Transform': [('Transform', 100, 1, 'OnHit')],
            'Splash': [('Splash', 100, 1, 'OnHit')],
            'Focus Energy': [('Focus Energy', 100, 1, 'OnHit')],
            'Teleport': [('Teleport', 100, 1, 'OnHit')],
            # Screen and Field Moves
            'Reflect': [('Reflect', 100, 1, 'OnHit')],
            'Light Screen': [('Light Screen', 100, 1, 'OnHit')],
            # =====================================================
            # ADDITIONAL MOVE EFFECTS (PokeAPI cross-reference)
            # =====================================================
            # --- High Crit Moves ---
            'Aeroblast': [('High Crit 1', 100, 1, 'OnHit')],
            'Air Cutter': [('High Crit 1', 100, 1, 'OnHit')],
            'Drill Run': [('High Crit 1', 100, 1, 'OnHit')],
            'Psycho Cut': [('High Crit 1', 100, 1, 'OnHit')],
            'Shadow Claw': [('High Crit 1', 100, 1, 'OnHit')],
            'Storm Throw': [('High Crit 1', 100, 1, 'OnHit')],
            'Blaze Kick': [('High Crit 1', 100, 1, 'OnHit'), ('Burn 10%', 10, 2, 'OnHit')],
            # --- Never Miss Moves ---
            'Disarming Voice': [('Never Miss', 100, 1, 'OnHit')],
            'Feint Attack': [('Never Miss', 100, 1, 'OnHit')],
            'Magical Leaf': [('Never Miss', 100, 1, 'OnHit')],
            'Shadow Punch': [('Never Miss', 100, 1, 'OnHit')],
            'Shock Wave': [('Never Miss', 100, 1, 'OnHit')],
            'Swift': [('Never Miss', 100, 1, 'OnHit')],
            'Vital Throw': [('Never Miss', 100, 1, 'OnHit')],
            'Pika Papow': [('Never Miss', 100, 1, 'OnHit')],
            'Veevee Volley': [('Never Miss', 100, 1, 'OnHit')],
            # --- Multi-Hit Moves ---
            'Arm Thrust': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            'Double Hit': [('Multi Hit 2', 100, 1, 'OnHit')],
            'Triple Kick': [('Multi Hit 3', 100, 1, 'OnHit')],
            'Beat Up': [('Multi Hit 2-5', 100, 1, 'OnHit')],
            # --- Stat Change Moves (User) ---
            'Autotomize': [('Raise Speed 2', 100, 1, 'OnHit')],
            'Cosmic Power': [('Raise Defense 1', 100, 1, 'OnHit'), ('Raise SpDefense 1', 100, 2, 'OnHit')],
            'Gear Up': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise SpAttack 1', 100, 2, 'OnHit')],
            'Howl': [('Raise Attack 1', 100, 1, 'OnHit')],
            'Stockpile': [('Raise Defense 1', 100, 1, 'OnHit'), ('Raise SpDefense 1', 100, 2, 'OnHit')],
            'Work Up': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise SpAttack 1', 100, 2, 'OnHit')],
            'Rototiller': [('Raise Attack 1', 100, 1, 'OnHit'), ('Raise SpAttack 1', 100, 2, 'OnHit')],
            'Aromatic Mist': [('Raise SpDefense 1', 100, 1, 'OnHit')],
            'Flower Shield': [('Raise Defense 1', 100, 1, 'OnHit')],
            'Steel Wing': [('Raise Defense 1', 10, 2, 'OnHit')],
            'Charge': [('Raise SpDefense 1', 100, 1, 'OnHit')],
            'Power-Up Punch': [('Raise Attack 1', 100, 2, 'OnHit')],
            'Fiery Dance': [('Raise SpAttack 1', 50, 2, 'OnHit')],
            'Charge Beam': [('Raise SpAttack 1', 70, 2, 'OnHit')],
            # --- Stat Change Moves (Target) ---
            'Charm': [('Lower Attack 2', 100, 1, 'OnHit')],
            'Captivate': [('Lower SpAttack 2', 100, 1, 'OnHit')],
            'Confide': [('Lower SpAttack 1', 100, 1, 'OnHit')],
            'Cotton Spore': [('Lower Speed 2', 100, 1, 'OnHit')],
            'Eerie Impulse': [('Lower SpAttack 2', 100, 1, 'OnHit')],
            'Fake Tears': [('Lower SpDefense 2', 100, 1, 'OnHit')],
            'Metal Sound': [('Lower SpDefense 2', 100, 1, 'OnHit')],
            'Noble Roar': [('Lower Attack 1', 100, 1, 'OnHit'), ('Lower SpAttack 1', 100, 2, 'OnHit')],
            'Scary Face': [('Lower Speed 2', 100, 1, 'OnHit')],
            'Sweet Scent': [('Lower Evasion 2', 100, 1, 'OnHit')],
            'Tearful Look': [('Lower Attack 1', 100, 1, 'OnHit'), ('Lower SpAttack 1', 100, 2, 'OnHit')],
            'Tickle': [('Lower Attack 1', 100, 1, 'OnHit'), ('Lower Defense 1', 100, 2, 'OnHit')],
            'Memento': [('Lower Attack 2', 100, 1, 'OnHit'), ('Lower SpAttack 2', 100, 2, 'OnHit'), ('Self Destruct', 100, 3, 'OnHit')],
            'Crush Claw': [('Lower Defense 1', 50, 2, 'OnHit')],
            'Iron Tail': [('Lower Defense 1', 30, 2, 'OnHit')],
            'Leaf Tornado': [('Lower Accuracy 1', 50, 2, 'OnHit')],
            'Mud-Slap': [('Lower Accuracy 1', 100, 2, 'OnHit')],
            'Muddy Water': [('Lower Accuracy 1', 30, 2, 'OnHit')],
            'Night Daze': [('Lower Accuracy 1', 40, 2, 'OnHit')],
            'Strength Sap': [('Lower Attack 1', 100, 1, 'OnHit'), ('Heal 50%', 100, 2, 'OnHit')],
            'Trop Kick': [('Lower Attack 1', 100, 2, 'OnHit')],
            # --- Status Ailment Moves ---
            'Buzzy Buzz': [('Paralysis 100%', 100, 2, 'OnHit')],
            'Flame Wheel': [('Burn 10%', 10, 2, 'OnHit')],
            'Force Palm': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Freeze-Dry': [('Freeze 10%', 10, 2, 'OnHit')],
            'Ice Fang': [('Freeze 10%', 10, 2, 'OnHit'), ('Flinch 10%', 10, 3, 'OnHit')],
            'Lava Plume': [('Burn 30%', 30, 2, 'OnHit')],
            'Poison Fang': [('Poison 40%', 40, 2, 'OnHit')],
            'Relic Song': [('Sleep', 10, 2, 'OnHit')],
            'Rock Climb': [('Confusion 20%', 20, 2, 'OnHit')],
            'Searing Shot': [('Burn 30%', 30, 2, 'OnHit')],
            'Sizzly Slide': [('Burn 100%', 100, 2, 'OnHit')],
            'Spark': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Splishy Splash': [('Paralysis 30%', 30, 2, 'OnHit')],
            'Steam Eruption': [('Burn 30%', 30, 2, 'OnHit')],
            'Thunder Fang': [('Paralysis 10%', 10, 2, 'OnHit'), ('Flinch 10%', 10, 3, 'OnHit')],
            'Water Pulse': [('Confusion 20%', 20, 2, 'OnHit')],
            'Dark Void': [('Sleep', 100, 1, 'OnHit')],
            'Grass Whistle': [('Sleep', 100, 1, 'OnHit')],
            'Teeter Dance': [('Confusion 100%', 100, 1, 'OnHit')],
            'Swagger': [('Confusion 100%', 100, 1, 'OnHit'), ('Raise Attack 2', 100, 2, 'OnHit')],
            'Flatter': [('Confusion 100%', 100, 1, 'OnHit'), ('Raise SpAttack 1', 100, 2, 'OnHit')],
            'Secret Power': [('Paralysis 30%', 30, 2, 'OnHit')],
            # --- Flinch Moves ---
            'Astonish': [('Flinch 30%', 30, 1, 'OnHit')],
            'Extrasensory': [('Flinch 10%', 10, 2, 'OnHit')],
            'Floaty Fall': [('Flinch 30%', 30, 2, 'OnHit')],
            'Snore': [('Flinch 30%', 30, 2, 'OnHit')],
            'Steamroller': [('Flinch 30%', 30, 2, 'OnHit')],
            'Twister': [('Flinch 20%', 20, 2, 'OnHit')],
            'Beak Blast': [('Burn 100%', 100, 2, 'OnHit')],
            # --- Drain / Heal Moves ---
            'Bouncy Bubble': [('Drain 75%', 100, 1, 'OnHit')],
            'Giga Drain': [('Drain 50%', 100, 1, 'OnHit')],
            'Floral Healing': [('Heal 50%', 100, 1, 'OnHit')],
            'Heal Pulse': [('Heal 50%', 100, 1, 'OnHit')],
            'Purify': [('Cure Status', 100, 1, 'OnHit'), ('Heal 50%', 100, 2, 'OnHit')],
            'Swallow': [('Heal 25%', 100, 1, 'OnHit')],
            'Refresh': [('Cure Status', 100, 1, 'OnHit')],
            'Healing Wish': [('Self Destruct', 100, 1, 'OnHit'), ('Heal 50%', 100, 2, 'OnHit')],
            'Lunar Dance': [('Self Destruct', 100, 1, 'OnHit'), ('Heal 50%', 100, 2, 'OnHit')],
            'Pollen Puff': [('Heal 50%', 100, 2, 'OnHit')],
            'Sparkling Aria': [('Cure Status', 100, 2, 'OnHit')],
            'Sparkly Swirl': [('Cure Status', 100, 2, 'OnHit')],
            # --- Recoil Moves ---
            'Head Charge': [('Recoil 25%', 100, 2, 'OnHit')],
            'Light of Ruin': [('Recoil 50%', 100, 2, 'OnHit')],
            'Struggle': [('Recoil 25%', 100, 2, 'OnHit')],
            # --- Recharge Moves ---
            'Frenzy Plant': [('Recharge Turn', 100, 2, 'OnHit')],
            'Hydro Cannon': [('Recharge Turn', 100, 2, 'OnHit')],
            # --- Speed / Priority Moves ---
            'Ally Switch': [('Priority +2', 100, 1, 'OnHit')],
            'Endure': [('Priority +2', 100, 1, 'OnHit')],
            'Sucker Punch': [('Priority +1', 100, 1, 'OnHit')],
            'Ion Deluge': [('Priority +1', 100, 1, 'OnHit')],
            'Zippy Zap': [('High Crit 1', 100, 1, 'OnHit'), ('Priority +2', 100, 2, 'OnHit')],
            'Follow Me': [('Priority +2', 100, 1, 'OnHit')],
            'Rage Powder': [('Priority +2', 100, 1, 'OnHit')],
            'Helping Hand': [('Priority +2', 100, 1, 'OnHit')],
            'Snatch': [('Priority +2', 100, 1, 'OnHit')],
            'Spotlight': [('Priority +2', 100, 1, 'OnHit')],
            'Crafty Shield': [('Protect', 100, 1, 'OnHit')],
            'Quick Guard': [('Protect', 100, 1, 'OnHit')],
            # --- Stat Lowering on Self (Offensive) ---
            'Superpower': [('Lower Attack 1', 100, 2, 'OnHit'), ('Lower Defense 1', 100, 3, 'OnHit')],
            'Hammer Arm': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Ice Hammer': [('Lower Speed 1', 100, 2, 'OnHit')],
            'V-create': [('Lower Defense 1', 100, 2, 'OnHit'), ('Lower SpDefense 1', 100, 3, 'OnHit'), ('Lower Speed 1', 100, 4, 'OnHit')],
            # --- Speed Lowering on Target ---
            'Electroweb': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Glaciate': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Icy Wind': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Low Sweep': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Rock Tomb': [('Lower Speed 1', 100, 2, 'OnHit')],
            'Rock Smash': [('Lower Defense 1', 50, 2, 'OnHit')],
            'Struggle Bug': [('Lower SpAttack 1', 100, 2, 'OnHit')],
            # --- Defog and Hazard Removal ---
            'Defog': [('Lower Evasion 1', 100, 1, 'OnHit'), ('Remove Hazards', 100, 2, 'OnHit')],
            'Psychic Fangs': [('Remove Hazards', 100, 2, 'OnHit')],
            'Brick Break': [('Remove Hazards', 100, 1, 'OnHit')],
            # --- Switch / U-turn Moves ---
            'U-turn': [('Switch Out', 100, 2, 'OnHit')],
            # --- Trap / Prevent Switching ---
            'Block': [('Prevent Switching', 100, 1, 'OnHit')],
            'Mean Look': [('Prevent Switching', 100, 1, 'OnHit')],
            'Spider Web': [('Prevent Switching', 100, 1, 'OnHit')],
            'Fairy Lock': [('Prevent Switching', 100, 1, 'OnHit')],
            'Thousand Waves': [('Prevent Switching', 100, 2, 'OnHit')],
            'Infestation': [('Trap 4-5 Turns', 100, 1, 'OnHit')],
            'Magma Storm': [('Trap 4-5 Turns', 100, 2, 'OnHit')],
            # --- Damage Modifier Moves ---
            'Assurance': [('Damage Doubling', 100, 1, 'OnHit')],
            'Avalanche': [('Damage Doubling', 100, 1, 'OnHit')],
            'Facade': [('Damage Doubling', 100, 1, 'OnHit')],
            'Hex': [('Damage Doubling', 100, 1, 'OnHit')],
            'Payback': [('Speed Dependent', 100, 1, 'OnHit')],
            'Retaliate': [('Damage Doubling', 100, 1, 'OnHit')],
            'Rollout': [('Damage Doubling', 100, 1, 'OnHit')],
            'Round': [('Damage Doubling', 100, 1, 'OnHit')],
            'Smelling Salts': [('Damage Doubling', 100, 1, 'OnHit')],
            'Stomping Tantrum': [('Damage Doubling', 100, 1, 'OnHit')],
            'Wake-Up Slap': [('Damage Doubling', 100, 1, 'OnHit')],
            'Fury Cutter': [('Damage Doubling', 100, 1, 'OnHit')],
            'Ice Ball': [('Damage Doubling', 100, 1, 'OnHit')],
            'Echoed Voice': [('Damage Doubling', 100, 1, 'OnHit')],
            'Fusion Flare': [('Damage Doubling', 100, 1, 'OnHit')],
            'Gyro Ball': [('Speed Dependent', 100, 1, 'OnHit')],
            # --- HP Scaling / Variable Power ---
            'Eruption': [('HP Scaling High', 100, 1, 'OnHit')],
            'Flail': [('HP Scaling High', 100, 1, 'OnHit')],
            'Reversal': [('HP Scaling High', 100, 1, 'OnHit')],
            'Crush Grip': [('HP Scaling High', 100, 1, 'OnHit')],
            'Wring Out': [('HP Scaling High', 100, 1, 'OnHit')],
            'Power Trip': [('Stat Boost Scaling', 100, 1, 'OnHit')],
            'Punishment': [('Stat Boost Scaling', 100, 1, 'OnHit')],
            "Nature's Madness": [('Fixed Damage 50% HP', 100, 1, 'OnHit')],
            'Heat Crash': [('Weight Damage', 100, 1, 'OnHit')],
            'Heavy Slam': [('Weight Damage', 100, 1, 'OnHit')],
            # --- Variable Power / Special Mechanics ---
            'Hidden Power': [('Variable Power', 100, 1, 'OnHit')],
            'Judgment': [('Variable Power', 100, 1, 'OnHit')],
            'Techno Blast': [('Variable Power', 100, 1, 'OnHit')],
            'Multi-Attack': [('Variable Power', 100, 1, 'OnHit')],
            'Revelation Dance': [('Variable Power', 100, 1, 'OnHit')],
            'Natural Gift': [('Variable Power', 100, 1, 'OnHit')],
            'Return': [('Variable Power', 100, 1, 'OnHit')],
            'Frustration': [('Variable Power', 100, 1, 'OnHit')],
            'Trump Card': [('Variable Power', 100, 1, 'OnHit')],
            'Last Resort': [('Variable Power', 100, 1, 'OnHit')],
            'Present': [('Variable Power', 100, 1, 'OnHit')],
            'False Swipe': [('Variable Power', 100, 1, 'OnHit')],
            'Hold Back': [('Variable Power', 100, 1, 'OnHit')],
            'Spit Up': [('Variable Power', 100, 1, 'OnHit')],
            'Doom Desire': [('Variable Power', 100, 1, 'OnHit')],
            'Future Sight': [('Variable Power', 100, 1, 'OnHit')],
            # --- Ignore Stat Changes ---
            'Chip Away': [('Ignore Stat Changes', 100, 1, 'OnHit')],
            'Sacred Sword': [('Ignore Stat Changes', 100, 1, 'OnHit')],
            'Foresight': [('Ignore Stat Changes', 100, 1, 'OnHit')],
            'Miracle Eye': [('Ignore Stat Changes', 100, 1, 'OnHit')],
            'Odor Sleuth': [('Ignore Stat Changes', 100, 1, 'OnHit')],
            # --- Stat Dependent Damage ---
            'Psyshock': [('Stat Dependent Damage', 100, 1, 'OnHit')],
            # --- Charge Turn Moves ---
            'Solar Blade': [('Charge Turn', 100, 1, 'OnHit')],
            # --- Self-Destruct / Faint Moves ---
            'Explosion': [('Self Destruct', 100, 1, 'OnHit')],
            'Self-Destruct': [('Self Destruct', 100, 1, 'OnHit')],
            # --- Already-Defined Effects ---
            'Attract': [('Attract', 100, 1, 'OnHit')],
            'Belly Drum': [('Belly Drum', 100, 1, 'OnHit')],
            'Conversion': [('Conversion', 100, 1, 'OnHit')],
            'Conversion 2': [('Conversion', 100, 1, 'OnHit')],
            'Copycat': [('Copycat', 100, 1, 'OnHit')],
            'Curse': [('Curse', 100, 1, 'OnHit')],
            'Destiny Bond': [('Destiny Bond', 100, 1, 'OnHit')],
            'Lucky Chant': [('Lucky Chant', 100, 1, 'OnHit')],
            'Nightmare': [('Nightmare', 100, 1, 'OnHit')],
            'Lock-On': [('Lock On', 100, 1, 'OnHit')],
            'Mind Reader': [('Lock On', 100, 1, 'OnHit')],
            'Pay Day': [('Pay Day', 100, 1, 'OnHit')],
            'Power Trick': [('Power Trick', 100, 1, 'OnHit')],
            'Power Swap': [('Power Swap', 100, 1, 'OnHit')],
            'Guard Swap': [('Guard Swap', 100, 1, 'OnHit')],
            'Guard Split': [('Guard Swap', 100, 1, 'OnHit')],
            'Power Split': [('Power Swap', 100, 1, 'OnHit')],
            'Heart Swap': [('Copy Stat Stages', 100, 1, 'OnHit')],
            'Spite': [('Spite', 100, 1, 'OnHit')],
            'Sticky Web': [('Sticky Web', 100, 1, 'OnHit')],
            'Tailwind': [('Tailwind', 100, 1, 'OnHit')],
            'Telekinesis': [('Telekinesis', 100, 1, 'OnHit')],
            'Topsy-Turvy': [('Clear Stats', 100, 1, 'OnHit')],
            'Laser Focus': [('Focus Energy', 100, 1, 'OnHit')],
            # --- Item / Ability Interaction ---
            'Thief': [('Remove Item', 100, 2, 'OnHit')],
            'Covet': [('Remove Item', 100, 2, 'OnHit')],
            'Fling': [('Remove Item', 100, 1, 'OnHit')],
            'Bug Bite': [('Remove Item', 100, 2, 'OnHit')],
            'Pluck': [('Remove Item', 100, 2, 'OnHit')],
            'Embargo': [('Remove Item', 100, 1, 'OnHit')],
            'Belch': [('Item Dependent', 100, 1, 'OnHit')],
            'Bestow': [('Swap Items', 100, 1, 'OnHit')],
            'Gastro Acid': [('Nullify Ability', 100, 1, 'OnHit')],
            'Entrainment': [('Nullify Ability', 100, 1, 'OnHit')],
            'Simple Beam': [('Nullify Ability', 100, 1, 'OnHit')],
            'Worry Seed': [('Nullify Ability', 100, 1, 'OnHit')],
            'Skill Swap': [('Nullify Ability', 100, 1, 'OnHit')],
            'Role Play': [('Nullify Ability', 100, 1, 'OnHit')],
            # --- Type Change Moves ---
            "Forest's Curse": [('Change Type Grass', 100, 1, 'OnHit')],
            'Electrify': [('Change Type Normal to Electric', 100, 1, 'OnHit')],
            'Reflect Type': [('Conversion', 100, 1, 'OnHit')],
            # --- Taunt/Protect/Status Prevention ---
            'Taunt': [('Taunt', 100, 1, 'OnHit')],
            'Mat Block': [('Protect', 100, 1, 'OnHit')],
            "King's Shield": [('Protect', 100, 1, 'OnHit'), ('Lower Attack 2', 100, 2, 'OnHit')],
            # --- Other Complex Moves ---
            'Outrage': [('Confusion', 100, 2, 'OnHit')],
            'Sky Drop': [('Fly', 100, 1, 'OnHit')],
            'Perish Song': [('Prevent Switching', 100, 1, 'OnHit')],
            'Acupressure': [('Raise All Stats 1', 100, 1, 'OnHit')],
            'Gravity': [('Lower Evasion 2', 100, 1, 'OnHit')],
            'Heal Block': [('Disable', 100, 1, 'OnHit')],
            'Imprison': [('Disable', 100, 1, 'OnHit')],
            'Instruct': [('Encore', 100, 1, 'OnHit')],
            'Pain Split': [('Heal 50%', 100, 1, 'OnHit')],
            'Psycho Shift': [('Cure Status', 100, 1, 'OnHit')],
            'High Jump Kick': [('Recoil 50%', 100, 2, 'IfMiss')],
            'Jump Kick': [('Recoil 50%', 100, 2, 'IfMiss')],
            'Nature Power': [('Variable Power', 100, 1, 'OnHit')],
            'Sleep Talk': [('Metronome', 100, 1, 'OnHit')],
            'Assist': [('Metronome', 100, 1, 'OnHit')],
            'Mimic': [('Copycat', 100, 1, 'OnHit')],
            'Uproar': [('Confusion', 100, 2, 'OnHit')],
            'Camouflage': [('Conversion', 100, 1, 'OnHit')],
            # --- Eevee/Pikachu Partner Moves ---
            'Baddy Bad': [('Reflect', 100, 2, 'OnHit')],
            'Sappy Seed': [('Trap 4-5 Turns', 100, 2, 'OnHit')],
            'Freezy Frost': [('Haze', 100, 2, 'OnHit')],
            'Glitzy Glow': [('Light Screen', 100, 2, 'OnHit')],
            'Thousand Arrows': [('Smack Down', 100, 2, 'OnHit')],
            'Magnet Rise': [('Raise Evasion 1', 100, 1, 'OnHit')],
            # --- No-Effect Moves (mapped to Splash) ---
            'Celebrate': [('Splash', 100, 1, 'OnHit')],
            'Hold Hands': [('Splash', 100, 1, 'OnHit')],
            'Happy Hour': [('Splash', 100, 1, 'OnHit')],
            'After You': [('Splash', 100, 1, 'OnHit')],
        }

        for move_name, effects in effects_map.items():
            move_id = get_move_id(move_name)
            if not move_id:
                continue

            for eff_tuple in effects:
                # Handle different tuple sizes if necessary, though our extractor ensures 4
                if len(eff_tuple) >= 4:
                    eff_name, prob, order, triggers = eff_tuple[:4]
                    eff_id = get_effect_id(eff_name)
                    if eff_id:
                        effect_instances.append((move_id, eff_id, prob, order, triggers))

        # Clear old and insert new
        cursor.execute('DELETE FROM move_effect_instances')
        cursor.executemany('''
            INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
            VALUES (?, ?, ?, ?, ?)
        ''', effect_instances)
        print(f'Inserted {len(effect_instances)} move effect instances')

    def _insert_move_effects(self, cursor):
        """Insert all move effects"""
        effects = [
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
            ('Poison 20%', '20% chance to inflict poison', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Poison 30%', '30% chance to inflict poison', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Poison 75%', '75% chance to inflict poison', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Poison 90%', '90% chance to inflict poison', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Poison 100%', 'Always poisons target', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Sleep', 'Puts target to sleep', 'STATUS', 'Sleep', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Confusion', 'Confuses target', 'STATUS', 'Confusion', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Confusion 100%', 'Always confuses target', 'STATUS', 'Confusion', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Raise Attack 1', 'Raises user Attack by 1 stage', 'STAT_CHANGE', 'None', 'Attack', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Attack 2', 'Raises user Attack by 2 stages', 'STAT_CHANGE', 'None', 'Attack', 2, 0, 0, 0, None, None, 'User'),
            ('Raise Defense 1', 'Raises user Defense by 1 stage', 'STAT_CHANGE', 'None', 'Defense', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Defense 2', 'Sharply raises Defense', 'STAT_CHANGE', 'None', 'Defense', 2, 0, 0, 0, None, None, 'User'),
            ('Raise SpAttack 1', 'Raises user Sp. Attack by 1 stage', 'STAT_CHANGE', 'None', 'SpAttack', 1, 0, 0, 0, None, None, 'User'),
            ('Raise SpAttack 2', 'Sharply raises Sp. Attack', 'STAT_CHANGE', 'None', 'SpAttack', 2, 0, 0, 0, None, None, 'User'),
            ('Raise SpAttack 3', 'Drastically raises Sp. Attack', 'STAT_CHANGE', 'None', 'SpAttack', 3, 0, 0, 0, None, None, 'User'),
            ('Raise SpDefense 1', 'Raises user Sp. Defense by 1 stage', 'STAT_CHANGE', 'None', 'SpDefense', 1, 0, 0, 0, None, None, 'User'),
            ('Raise SpDefense 2', 'Sharply raises Sp. Defense', 'STAT_CHANGE', 'None', 'SpDefense', 2, 0, 0, 0, None, None, 'User'),
            ('Raise Speed 1', 'Raises user Speed by 1 stage', 'STAT_CHANGE', 'None', 'Speed', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Speed 2', 'Raises user Speed by 2 stages', 'STAT_CHANGE', 'None', 'Speed', 2, 0, 0, 0, None, None, 'User'),
            ('Raise Accuracy 1', 'Raises user Accuracy by 1 stage', 'STAT_CHANGE', 'None', 'Accuracy', 1, 0, 0, 0, None, None, 'User'),
            ('Raise All Stats 1', 'Raises all user stats by 1 stage', 'STAT_CHANGE', 'None', 'All', 1, 0, 0, 0, None, None, 'User'),
            ('Lower Attack 1', 'Lowers target Attack by 1 stage', 'STAT_CHANGE', 'None', 'Attack', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower Attack 2', 'Sharply lowers Attack', 'STAT_CHANGE', 'None', 'Attack', -2, 0, 0, 0, None, None, 'Target'),
            ('Lower Defense 1', 'Lowers target Defense by 1 stage', 'STAT_CHANGE', 'None', 'Defense', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower Defense 2', 'Sharply lowers Defense', 'STAT_CHANGE', 'None', 'Defense', -2, 0, 0, 0, None, None, 'Target'),
            ('Lower SpAttack 1', 'Lowers target Sp. Attack by 1 stage', 'STAT_CHANGE', 'None', 'SpAttack', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower SpAttack 2', 'Sharply lowers Sp. Attack', 'STAT_CHANGE', 'None', 'SpAttack', -2, 0, 0, 0, None, None, 'Target'),
            ('Lower SpDefense 1', 'Lowers target Sp. Defense by 1 stage', 'STAT_CHANGE', 'None', 'SpDefense', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower SpDefense 2', 'Sharply lowers Sp. Defense', 'STAT_CHANGE', 'None', 'SpDefense', -2, 0, 0, 0, None, None, 'Target'),
            ('Lower Speed 1', 'Lowers target Speed by 1 stage', 'STAT_CHANGE', 'None', 'Speed', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower Accuracy 1', 'Lowers target Accuracy by 1 stage', 'STAT_CHANGE', 'None', 'Accuracy', -1, 0, 0, 0, None, None, 'Target'),
            ('Clear Stats', 'Resets all stat changes', 'STAT_CHANGE', 'None', 'All', 0, 0, 0, 0, None, None, 'Target'),
            ('Heal 25%', 'Heals user by 25% of max HP', 'HEAL', 'None', None, 0, 25, 0, 0, None, None, 'User'),
            ('Heal 50%', 'Heals user by 50% of max HP', 'HEAL', 'None', None, 0, 50, 0, 0, None, None, 'User'),
            ('Drain 50%', 'Drains 50% of damage dealt', 'HEAL', 'None', None, 0, 50, 0, 0, None, None, 'User'),
            ('Drain 75%', 'Drains 75% of damage dealt', 'HEAL', 'None', None, 0, 75, 0, 0, None, None, 'User'),
            ('Cure Status', 'Cures status conditions', 'HEAL', 'None', None, 0, 0, 0, 0, None, None, 'UserSide'),
            ('Wish', 'Heals 50% HP next turn', 'HEAL', 'None', None, 0, 50, 0, 0, None, None, 'User'),
            ('Ingrain', 'Heals 1/16 HP per turn, cannot switch', 'HEAL', 'None', None, 0, 6, 0, 0, None, None, 'User'),
            ('Aqua Ring', 'Heals 1/16 HP per turn', 'HEAL', 'None', None, 0, 6, 0, 0, None, None, 'User'),
            ('Recoil 25%', 'User takes 25% recoil damage', 'RECOIL', 'None', None, 0, 0, 0, 25, None, None, 'User'),
            ('Recoil 33%', 'User takes 33% recoil damage', 'RECOIL', 'None', None, 0, 0, 0, 33, None, None, 'User'),
            ('Recoil 50%', 'User takes 50% recoil damage', 'RECOIL', 'None', None, 0, 0, 0, 50, None, None, 'User'),
            ('Self HP Cost 50%', 'User loses 50% HP', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Set Sun', 'Sets harsh sunlight for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Sun', None, 'Field'),
            ('Set Rain', 'Sets rain for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Rain', None, 'Field'),
            ('Set Sandstorm', 'Sets sandstorm for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Sandstorm', None, 'Field'),
            ('Set Hail', 'Sets hail for 5 turns', 'WEATHER', 'None', None, 0, 0, 0, 0, 'Hail', None, 'Field'),
            ('Set Spikes', 'Sets spikes on opponent side', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'Spikes', 'TargetSide'),
            ('Set Toxic Spikes', 'Sets toxic spikes on opponent side', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'ToxicSpikes', 'TargetSide'),
            ('Set Stealth Rock', 'Sets stealth rocks on opponent side', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'StealthRock', 'TargetSide'),
            ('Sticky Web', 'Sets sticky web on opponent side', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'StickyWeb', 'TargetSide'),
            ('Trick Room', 'Slower Pokemon move first for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'TrickRoom', 'Field'),
            ('Tailwind', 'Doubles Speed for 4 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'Tailwind', 'UserSide'),
            ('Electric Terrain', 'Sets Electric Terrain for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'ElectricTerrain', 'Field'),
            ('Grassy Terrain', 'Sets Grassy Terrain for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'GrassyTerrain', 'Field'),
            ('Misty Terrain', 'Sets Misty Terrain for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'MistyTerrain', 'Field'),
            ('Psychic Terrain', 'Sets Psychic Terrain for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'PsychicTerrain', 'Field'),
            ('Aurora Veil', 'Reduces damage for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'AuroraVeil', 'UserSide'),
            ('Wide Guard', 'Protects from spread moves', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'WideGuard', 'UserSide'),
            ('Court Change', 'Switches field effects with opponent', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'CourtChange', 'Field'),
            ('Remove Hazards', 'Removes hazards from field', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'RemoveHazards', 'UserSide'),
            ('Safeguard', 'Prevents status conditions for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'Safeguard', 'UserSide'),
            ('Mist', 'Prevents stat lowering for 5 turns', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'Mist', 'UserSide'),
            ('Haze', 'Resets all stat changes', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'Haze', 'Field'),
            ('Flinch', 'Causes target to flinch', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Always Crit', 'Always results in a critical hit', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Priority +1', 'Increased priority', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Priority +2', 'High priority', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Protect', 'Protects user from attacks', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('OHKO', 'One-hit KO if it hits', 'OTHER', 'None', None, 0, 0, 0, 0, None, 'OHKO', 'Target'),
            ('Variable Power', 'Power varies based on conditions', 'OTHER', 'None', None, 0, 0, 0, 0, None, 'VariablePower', 'Target'),
            ('Multi Hit 2', 'Hits 2 times', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Multi Hit 3', 'Hits 3 times', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Multi Hit 2-5', 'Hits 2-5 times', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Recharge Turn', 'User cannot move next turn', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
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
            ('Change Type Ghost', 'Adds Ghost type to target', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Change Type Normal to Electric', 'Changes Normal moves to Electric', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Field'),
            ('Change Type Fire Weakness', 'Makes target weak to Fire', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Damage Contact', 'Damages contact attackers', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Prevent Sound Moves', 'Prevents target from using sound moves', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Use Target Attack', 'Uses target Attack stat for damage', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Type Dependent', 'Only hits Pokémon sharing type with user', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Damage Doubling', 'Double power if used after specific move', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Pursuit Damage', 'Double power if target is switching out', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Smack Down', 'Grounds target', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Speed Swap', 'Swaps Speed stat with target', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Steal Stat Boosts', 'Steals targets positive stat changes', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Copy Stat Stages', 'Copies target stat stages', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Swap Items', 'Swaps held items with target', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('HP Scaling High', 'More power at higher HP', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Speed Dependent', 'Double power if user attacks first', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Stat Dependent Damage', 'Uses higher of Attack or Sp. Attack', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Terrain Dependent', 'Effect changes with active terrain', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Stat Boost Scaling', '+20 power per stat boost', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Create Substitute', 'Creates substitute with 1/4 max HP', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Encore', 'Forces target to repeat last move for 3 turns', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Disable', 'Disables target last move for 4 turns', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Torment', 'Target cannot use same move twice in a row', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Yawn', 'Target falls asleep next turn', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Baton Pass', 'Switches out, passes stat changes', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Lower Speed 2', 'Sharply lowers Speed', 'STAT_CHANGE', 'None', 'Speed', -2, 0, 0, 0, None, None, 'Target'),
            ('Raise Evasion 1', 'Raises user Evasion by 1 stage', 'STAT_CHANGE', 'None', 'Evasion', 1, 0, 0, 0, None, None, 'User'),
            ('Raise Evasion 2', 'Sharply raises Evasion', 'STAT_CHANGE', 'None', 'Evasion', 2, 0, 0, 0, None, None, 'User'),
            ('Lower Evasion 1', 'Lowers target Evasion by 1 stage', 'STAT_CHANGE', 'None', 'Evasion', -1, 0, 0, 0, None, None, 'Target'),
            ('Lower Evasion 2', 'Sharply lowers Evasion', 'STAT_CHANGE', 'None', 'Evasion', -2, 0, 0, 0, None, None, 'Target'),
            ('Raise Defense 3', 'Drastically raises Defense', 'STAT_CHANGE', 'None', 'Defense', 3, 0, 0, 0, None, None, 'User'),
            ('Poison 40%', '40% chance to poison', 'STATUS', 'Poison', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Focus Energy', 'Increases critical hit ratio', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Taunt', 'Prevents status moves', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Attract', 'Infatuates opponent', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Belly Drum', 'Cuts HP to max Attack', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Transform', 'Copies opponent', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Metronome', 'Uses random move', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Mirror Move', 'Copies last move', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Conversion', 'Changes type to texture', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Lock On', 'Next hit guarantees hit', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Destiny Bond', 'Faints opponent if user faints', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Spite', 'Lowers PP of last move', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Nightmare', 'Damages sleeping opponent', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Curse', 'Ghost: cuts HP to curse; Else: lowers speed, raises atk/def', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Lucky Chant', 'Prevents crit hits', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'LuckyChant', 'UserSide'),
            ('Light Screen', 'Special damage reduced', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'LightScreen', 'UserSide'),
            ('Reflect', 'Physical damage reduced', 'FIELD_EFFECT', 'None', None, 0, 0, 0, 0, None, 'Reflect', 'UserSide'),
            ('Power Trick', 'Swaps Attack and Defense', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Copycat', 'Uses last move used in battle', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Power Swap', 'Swaps Attack/SpAttack changes', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Guard Swap', 'Swaps Defense/SpDefense changes', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Pay Day', 'Scatter coins', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Telekinesis', 'Makes target float', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Confusion 10%', 'Chance to confuse', 'STATUS', 'Confusion', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Confusion 20%', 'Chance to confuse', 'STATUS', 'Confusion', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Confusion 30%', 'Chance to confuse', 'STATUS', 'Confusion', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Flinch 10%', 'Chance to flinch', 'OTHER', None, None, 0, 0, 0, 0, None, None, 'Target'),
            ('Flinch 20%', 'Chance to flinch', 'OTHER', None, None, 0, 0, 0, 0, None, None, 'Target'),
            ('Flinch 30%', 'Chance to flinch', 'OTHER', None, None, 0, 0, 0, 0, None, None, 'Target'),
            ('Heal Bell', 'Cures party status', 'HEAL', None, None, 0, 0, 0, 0, None, None, 'UserSide'),
            ('High Crit 1', 'High critical hit ratio', 'OTHER', None, None, 0, 0, 0, 0, None, None, 'User'),
            ('Raise accuracy 1', 'Raises Accuracy by 1', 'STAT_CHANGE', None, 'Accuracy', 1, 0, 0, 0, None, None, 'User'),
            ('Self Destruct', 'User faints', 'OTHER', None, None, 0, 0, 0, 0, None, None, 'User'),
            ('Sleep 100%', 'Chance to sleep', 'STATUS', 'Sleep', None, 0, 0, 0, 0, None, None, 'Target'),
            # Complex Move Effects
            ('Charge Turn', 'User spends turn charging', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Dig', 'Digs underground turn 1', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Fly', 'Flies up turn 1', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Dive', 'Dives underwater turn 1', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Shadow Force', 'Vanishes instantly turn 1', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Fixed Damage Level', 'Deals damage equal to level', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Fixed Damage 20', 'Deals exactly 20 HP damage', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Fixed Damage 40', 'Deals exactly 40 HP damage', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Fixed Damage 50% HP', 'Deals damage equal to 50% of target current HP', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Fixed Damage Random', 'Deals damage between 50-150% of user level', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Weight Damage', 'Damage based on target weight', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Counter', 'Returns physical damage double', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Mirror Coat', 'Returns special damage double', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Metal Burst', 'Returns last damage taken 1.5x', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Bide', 'Endures attacks then returns damage', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Endeavor', 'Reduces target HP to match user HP', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Final Gambit', 'User faints, deals damage equal to HP', 'DAMAGE_MODIFIER', 'None', None, 0, 0, 0, 0, None, None, 'Target'),
            ('Splash', 'No effect', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
            ('Teleport', 'Switch out or flee', 'OTHER', 'None', None, 0, 0, 0, 0, None, None, 'User'),
        ]
        cursor.executemany('''
        INSERT INTO move_effects 
        (name, description, effect_type, status_condition, stat_to_change, stat_change_amount, 
         heal_percentage, heal_fixed_amount, recoil_percentage, weather_type, field_condition, effect_target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', effects)

    def _insert_moves(self, cursor):
        """Insert ALL 724 moves from Gen 1-7"""
        moves = [
            (1, 'Pound', 'Normal', 'Physical', 35, 40, 100, True, True, 0, 'Normal', 'Pound - Physical Normal move.'),
            (2, 'Karate Chop', 'Fighting', 'Physical', 25, 50, 100, True, True, 0, 'Normal', 'Karate Chop - Physical Fighting move.'),
            (3, 'Double Slap', 'Normal', 'Physical', 10, 15, 85, True, True, 0, 'Normal', 'Double Slap - Physical Normal move.'),
            (4, 'Comet Punch', 'Normal', 'Physical', 15, 18, 85, True, True, 0, 'Normal', 'Comet Punch - Physical Normal move.'),
            (5, 'Mega Punch', 'Normal', 'Physical', 20, 80, 85, True, True, 0, 'Normal', 'Mega Punch - Physical Normal move.'),
            (6, 'Pay Day', 'Normal', 'Physical', 20, 40, 100, True, True, 0, 'Normal', 'Pay Day - Physical Normal move.'),
            (7, 'Fire Punch', 'Fire', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'Fire Punch - Physical Fire move.'),
            (8, 'Ice Punch', 'Ice', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'Ice Punch - Physical Ice move.'),
            (9, 'Thunder Punch', 'Electric', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'Thunder Punch - Physical Electric move.'),
            (10, 'Scratch', 'Normal', 'Physical', 35, 40, 100, True, True, 0, 'Normal', 'Scratch - Physical Normal move.'),
            (11, 'Vise Grip', 'Normal', 'Physical', 30, 55, 100, True, True, 0, 'Normal', 'Vise Grip - Physical Normal move.'),
            (12, 'Guillotine', 'Normal', 'Physical', 5, None, 30, False, True, 0, 'Normal', 'Guillotine - Physical Normal move.'),
            (13, 'Razor Wind', 'Normal', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Razor Wind - Special Normal move.'),
            (14, 'Swords Dance', 'Normal', 'Status', 20, None, None, False, False, 0, 'Self', 'Swords Dance - Status Normal move.'),
            (15, 'Cut', 'Normal', 'Physical', 30, 50, 95, True, True, 0, 'Normal', 'Cut - Physical Normal move.'),
            (16, 'Gust', 'Flying', 'Special', 35, 40, 100, True, False, 0, 'Normal', 'Gust - Special Flying move.'),
            (17, 'Wing Attack', 'Flying', 'Physical', 35, 60, 100, True, True, 0, 'Normal', 'Wing Attack - Physical Flying move.'),
            (18, 'Whirlwind', 'Normal', 'Status', 20, None, None, False, False, -6, 'Normal', 'Whirlwind - Status Normal move.'),
            (19, 'Fly', 'Flying', 'Physical', 15, 90, 95, True, True, 0, 'Normal', 'Fly - Physical Flying move.'),
            (20, 'Bind', 'Normal', 'Physical', 20, 15, 85, True, True, 0, 'Normal', 'Bind - Physical Normal move.'),
            (21, 'Slam', 'Normal', 'Physical', 20, 80, 75, True, True, 0, 'Normal', 'Slam - Physical Normal move.'),
            (22, 'Vine Whip', 'Grass', 'Physical', 25, 45, 100, True, True, 0, 'Normal', 'Vine Whip - Physical Grass move.'),
            (23, 'Stomp', 'Normal', 'Physical', 20, 65, 100, True, True, 0, 'Normal', 'Stomp - Physical Normal move.'),
            (24, 'Double Kick', 'Fighting', 'Physical', 30, 30, 100, True, True, 0, 'Normal', 'Double Kick - Physical Fighting move.'),
            (25, 'Mega Kick', 'Normal', 'Physical', 5, 120, 75, True, True, 0, 'Normal', 'Mega Kick - Physical Normal move.'),
            (26, 'Jump Kick', 'Fighting', 'Physical', 10, 100, 95, True, True, 0, 'Normal', 'Jump Kick - Physical Fighting move.'),
            (27, 'Rolling Kick', 'Fighting', 'Physical', 15, 60, 85, True, True, 0, 'Normal', 'Rolling Kick - Physical Fighting move.'),
            (28, 'Sand Attack', 'Ground', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Sand Attack - Status Ground move.'),
            (29, 'Headbutt', 'Normal', 'Physical', 15, 70, 100, True, True, 0, 'Normal', 'Headbutt - Physical Normal move.'),
            (30, 'Horn Attack', 'Normal', 'Physical', 25, 65, 100, True, True, 0, 'Normal', 'Horn Attack - Physical Normal move.'),
            (31, 'Fury Attack', 'Normal', 'Physical', 20, 15, 85, True, True, 0, 'Normal', 'Fury Attack - Physical Normal move.'),
            (32, 'Horn Drill', 'Normal', 'Physical', 5, None, 30, False, True, 0, 'Normal', 'Horn Drill - Physical Normal move.'),
            (33, 'Tackle', 'Normal', 'Physical', 35, 40, 100, True, True, 0, 'Normal', 'Tackle - Physical Normal move.'),
            (34, 'Body Slam', 'Normal', 'Physical', 15, 85, 100, True, True, 0, 'Normal', 'Body Slam - Physical Normal move.'),
            (35, 'Wrap', 'Normal', 'Physical', 20, 15, 90, True, True, 0, 'Normal', 'Wrap - Physical Normal move.'),
            (36, 'Take Down', 'Normal', 'Physical', 20, 90, 85, True, True, 0, 'Normal', 'Take Down - Physical Normal move.'),
            (37, 'Thrash', 'Normal', 'Physical', 10, 120, 100, True, True, 0, 'Random_Opponent', 'Thrash - Physical Normal move.'),
            (38, 'Double-Edge', 'Normal', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'Double-Edge - Physical Normal move.'),
            (39, 'Tail Whip', 'Normal', 'Status', 30, None, 100, False, False, 0, 'Normal', 'Tail Whip - Status Normal move.'),
            (40, 'Poison Sting', 'Poison', 'Physical', 35, 15, 100, True, True, 0, 'Normal', 'Poison Sting - Physical Poison move.'),
            (41, 'Twineedle', 'Bug', 'Physical', 20, 25, 100, True, True, 0, 'Normal', 'Twineedle - Physical Bug move.'),
            (42, 'Pin Missile', 'Bug', 'Physical', 20, 25, 95, True, True, 0, 'Normal', 'Pin Missile - Physical Bug move.'),
            (43, 'Leer', 'Normal', 'Status', 30, None, 100, False, False, 0, 'Normal', 'Leer - Status Normal move.'),
            (44, 'Bite', 'Dark', 'Physical', 25, 60, 100, True, True, 0, 'Normal', 'Bite - Physical Dark move.'),
            (45, 'Growl', 'Normal', 'Status', 40, None, 100, False, False, 0, 'Normal', 'Growl - Status Normal move.'),
            (46, 'Roar', 'Normal', 'Status', 20, None, None, False, False, -6, 'Normal', 'Roar - Status Normal move.'),
            (47, 'Sing', 'Normal', 'Status', 15, None, 55, False, False, 0, 'Normal', 'Sing - Status Normal move.'),
            (48, 'Supersonic', 'Normal', 'Status', 20, None, 55, False, False, 0, 'Normal', 'Supersonic - Status Normal move.'),
            (49, 'Sonic Boom', 'Normal', 'Special', 20, None, 90, False, False, 0, 'Normal', 'Sonic Boom - Special Normal move.'),
            (50, 'Disable', 'Normal', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Disable - Status Normal move.'),
            (51, 'Acid', 'Poison', 'Special', 30, 40, 100, True, False, 0, 'Normal', 'Acid - Special Poison move.'),
            (52, 'Ember', 'Fire', 'Special', 25, 40, 100, True, False, 0, 'Normal', 'Ember - Special Fire move.'),
            (53, 'Flamethrower', 'Fire', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'Flamethrower - Special Fire move.'),
            (54, 'Mist', 'Ice', 'Status', 30, None, None, False, False, 0, 'UserSide', 'Mist - Status Ice move.'),
            (55, 'Water Gun', 'Water', 'Special', 25, 40, 100, True, False, 0, 'Normal', 'Water Gun - Special Water move.'),
            (56, 'Hydro Pump', 'Water', 'Special', 5, 110, 80, True, False, 0, 'Normal', 'Hydro Pump - Special Water move.'),
            (57, 'Surf', 'Water', 'Special', 15, 90, 100, True, False, 0, 'All_Adjacent', 'Surf - Special Water move.'),
            (58, 'Ice Beam', 'Ice', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Ice Beam - Special Ice move.'),
            (59, 'Blizzard', 'Ice', 'Special', 5, 110, 70, True, False, 0, 'All_Adjacent_Foes', 'Blizzard - Special Ice move.'),
            (60, 'Psybeam', 'Psychic', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'Psybeam - Special Psychic move.'),
            (61, 'Bubble Beam', 'Water', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'Bubble Beam - Special Water move.'),
            (62, 'Aurora Beam', 'Ice', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'Aurora Beam - Special Ice move.'),
            (63, 'Hyper Beam', 'Normal', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'Hyper Beam - Special Normal move.'),
            (64, 'Peck', 'Flying', 'Physical', 35, 35, 100, True, True, 0, 'Normal', 'Peck - Physical Flying move.'),
            (65, 'Drill Peck', 'Flying', 'Physical', 20, 80, 100, True, True, 0, 'Normal', 'Drill Peck - Physical Flying move.'),
            (66, 'Submission', 'Fighting', 'Physical', 20, 80, 80, True, True, 0, 'Normal', 'Submission - Physical Fighting move.'),
            (67, 'Low Kick', 'Fighting', 'Physical', 20, None, 100, False, True, 0, 'Normal', 'Low Kick - Physical Fighting move.'),
            (68, 'Counter', 'Fighting', 'Physical', 20, None, 100, False, True, -5, 'Normal', 'Counter - Physical Fighting move.'),
            (69, 'Seismic Toss', 'Fighting', 'Physical', 20, None, 100, False, True, 0, 'Normal', 'Seismic Toss - Physical Fighting move.'),
            (70, 'Strength', 'Normal', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Strength - Physical Normal move.'),
            (71, 'Absorb', 'Grass', 'Special', 25, 20, 100, True, False, 0, 'Normal', 'Absorb - Special Grass move.'),
            (72, 'Mega Drain', 'Grass', 'Special', 15, 40, 100, True, False, 0, 'Normal', 'Mega Drain - Special Grass move.'),
            (73, 'Leech Seed', 'Grass', 'Status', 10, None, 90, False, False, 0, 'Normal', 'Leech Seed - Status Grass move.'),
            (74, 'Growth', 'Normal', 'Status', 20, None, None, False, False, 0, 'Self', 'Growth - Status Normal move.'),
            (75, 'Razor Leaf', 'Grass', 'Physical', 25, 55, 95, True, True, 0, 'All_Adjacent_Foes', 'Razor Leaf - Physical Grass move.'),
            (76, 'Solar Beam', 'Grass', 'Special', 10, 120, 100, True, False, 0, 'Normal', 'Solar Beam - Special Grass move.'),
            (77, 'Poison Powder', 'Poison', 'Status', 35, None, 75, False, False, 0, 'Normal', 'Poison Powder - Status Poison move.'),
            (78, 'Stun Spore', 'Grass', 'Status', 30, None, 75, False, False, 0, 'Normal', 'Stun Spore - Status Grass move.'),
            (79, 'Sleep Powder', 'Grass', 'Status', 15, None, 75, False, False, 0, 'Normal', 'Sleep Powder - Status Grass move.'),
            (80, 'Petal Dance', 'Grass', 'Special', 10, 120, 100, True, False, 0, 'Random_Opponent', 'Petal Dance - Special Grass move.'),
            (81, 'String Shot', 'Bug', 'Status', 40, None, 95, False, False, 0, 'Normal', 'String Shot - Status Bug move.'),
            (82, 'Dragon Rage', 'Dragon', 'Special', 10, None, 100, False, False, 0, 'Normal', 'Dragon Rage - Special Dragon move.'),
            (83, 'Fire Spin', 'Fire', 'Special', 15, 35, 85, True, False, 0, 'Normal', 'Fire Spin - Special Fire move.'),
            (84, 'Thunder Shock', 'Electric', 'Special', 30, 40, 100, True, False, 0, 'Normal', 'Thunder Shock - Special Electric move.'),
            (85, 'Thunderbolt', 'Electric', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'Thunderbolt - Special Electric move.'),
            (86, 'Thunder Wave', 'Electric', 'Status', 20, None, 90, False, False, 0, 'Normal', 'Thunder Wave - Status Electric move.'),
            (87, 'Thunder', 'Electric', 'Special', 10, 110, 70, True, False, 0, 'Normal', 'Thunder - Special Electric move.'),
            (88, 'Rock Throw', 'Rock', 'Physical', 15, 50, 90, True, True, 0, 'Normal', 'Rock Throw - Physical Rock move.'),
            (89, 'Earthquake', 'Ground', 'Physical', 10, 100, 100, True, True, 0, 'All_Adjacent', 'Earthquake - Physical Ground move.'),
            (90, 'Fissure', 'Ground', 'Physical', 5, None, 30, False, True, 0, 'Normal', 'Fissure - Physical Ground move.'),
            (91, 'Dig', 'Ground', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Dig - Physical Ground move.'),
            (92, 'Toxic', 'Poison', 'Status', 10, None, 90, False, False, 0, 'Normal', 'Toxic - Status Poison move.'),
            (93, 'Confusion', 'Psychic', 'Special', 25, 50, 100, True, False, 0, 'Normal', 'Confusion - Special Psychic move.'),
            (94, 'Psychic', 'Psychic', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Psychic - Special Psychic move.'),
            (95, 'Hypnosis', 'Psychic', 'Status', 20, None, 60, False, False, 0, 'Normal', 'Hypnosis - Status Psychic move.'),
            (96, 'Meditate', 'Psychic', 'Status', 40, None, None, False, False, 0, 'Normal', 'Meditate - Status Psychic move.'),
            (97, 'Agility', 'Psychic', 'Status', 30, None, None, False, False, 0, 'Self', 'Agility - Status Psychic move.'),
            (98, 'Quick Attack', 'Normal', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'Quick Attack - Physical Normal move.'),
            (99, 'Rage', 'Normal', 'Physical', 20, 20, 100, True, True, 0, 'Normal', 'Rage - Physical Normal move.'),
            (100, 'Teleport', 'Psychic', 'Status', 20, None, None, False, False, 0, 'Normal', 'Teleport - Status Psychic move.'),
            (101, 'Night Shade', 'Ghost', 'Special', 15, None, 100, False, False, 0, 'Normal', 'Night Shade - Special Ghost move.'),
            (102, 'Mimic', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Mimic - Status Normal move.'),
            (103, 'Screech', 'Normal', 'Status', 40, None, 85, False, False, 0, 'Normal', 'Screech - Status Normal move.'),
            (104, 'Double Team', 'Normal', 'Status', 15, None, None, False, False, 0, 'Self', 'Double Team - Status Normal move.'),
            (105, 'Recover', 'Normal', 'Status', 5, None, None, False, False, 0, 'Self', 'Recover - Status Normal move.'),
            (106, 'Harden', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Harden - Status Normal move.'),
            (107, 'Minimize', 'Normal', 'Status', 10, None, None, False, False, 0, 'Self', 'Minimize - Status Normal move.'),
            (108, 'Smokescreen', 'Normal', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Smokescreen - Status Normal move.'),
            (109, 'Confuse Ray', 'Ghost', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Confuse Ray - Status Ghost move.'),
            (110, 'Withdraw', 'Water', 'Status', 40, None, None, False, False, 0, 'Normal', 'Withdraw - Status Water move.'),
            (111, 'Defense Curl', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Defense Curl - Status Normal move.'),
            (112, 'Barrier', 'Psychic', 'Status', 20, None, None, False, False, 0, 'Normal', 'Barrier - Status Psychic move.'),
            (113, 'Light Screen', 'Psychic', 'Status', 30, None, None, False, False, 0, 'UserSide', 'Light Screen - Status Psychic move.'),
            (114, 'Haze', 'Ice', 'Status', 30, None, None, False, False, 0, 'Normal', 'Haze - Status Ice move.'),
            (115, 'Reflect', 'Psychic', 'Status', 20, None, None, False, False, 0, 'UserSide', 'Reflect - Status Psychic move.'),
            (116, 'Focus Energy', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Focus Energy - Status Normal move.'),
            (117, 'Bide', 'Normal', 'Physical', 10, None, None, False, True, 0, 'Normal', 'Bide - Physical Normal move.'),
            (118, 'Metronome', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Metronome - Status Normal move.'),
            (119, 'Mirror Move', 'Flying', 'Status', 20, None, None, False, False, 0, 'Normal', 'Mirror Move - Status Flying move.'),
            (120, 'Self-Destruct', 'Normal', 'Physical', 5, 200, 100, True, True, 0, 'All_Adjacent', 'Self-Destruct - Physical Normal move.'),
            (121, 'Egg Bomb', 'Normal', 'Physical', 10, 100, 75, True, True, 0, 'Normal', 'Egg Bomb - Physical Normal move.'),
            (122, 'Lick', 'Ghost', 'Physical', 30, 30, 100, True, True, 0, 'Normal', 'Lick - Physical Ghost move.'),
            (123, 'Smog', 'Poison', 'Special', 20, 30, 70, True, False, 0, 'Normal', 'Smog - Special Poison move.'),
            (124, 'Sludge', 'Poison', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'Sludge - Special Poison move.'),
            (125, 'Bone Club', 'Ground', 'Physical', 20, 65, 85, True, True, 0, 'Normal', 'Bone Club - Physical Ground move.'),
            (126, 'Fire Blast', 'Fire', 'Special', 5, 110, 85, True, False, 0, 'Normal', 'Fire Blast - Special Fire move.'),
            (127, 'Waterfall', 'Water', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Waterfall - Physical Water move.'),
            (128, 'Clamp', 'Water', 'Physical', 15, 35, 85, True, True, 0, 'Normal', 'Clamp - Physical Water move.'),
            (129, 'Swift', 'Normal', 'Special', 20, 60, None, True, False, 0, 'Normal', 'Swift - Special Normal move.'),
            (130, 'Skull Bash', 'Normal', 'Physical', 10, 130, 100, True, True, 0, 'Normal', 'Skull Bash - Physical Normal move.'),
            (131, 'Spike Cannon', 'Normal', 'Physical', 15, 20, 100, True, True, 0, 'Normal', 'Spike Cannon - Physical Normal move.'),
            (132, 'Constrict', 'Normal', 'Physical', 35, 10, 100, True, True, 0, 'Normal', 'Constrict - Physical Normal move.'),
            (133, 'Amnesia', 'Psychic', 'Status', 20, None, None, False, False, 0, 'Self', 'Amnesia - Status Psychic move.'),
            (134, 'Kinesis', 'Psychic', 'Status', 15, None, 80, False, False, 0, 'Normal', 'Kinesis - Status Psychic move.'),
            (135, 'Soft-Boiled', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Soft-Boiled - Status Normal move.'),
            (136, 'High Jump Kick', 'Fighting', 'Physical', 10, 130, 90, True, True, 0, 'Normal', 'High Jump Kick - Physical Fighting move.'),
            (137, 'Glare', 'Normal', 'Status', 30, None, 100, False, False, 0, 'Normal', 'Glare - Status Normal move.'),
            (138, 'Dream Eater', 'Psychic', 'Special', 15, 100, 100, True, False, 0, 'Normal', 'Dream Eater - Special Psychic move.'),
            (139, 'Poison Gas', 'Poison', 'Status', 40, None, 90, False, False, 0, 'Normal', 'Poison Gas - Status Poison move.'),
            (140, 'Barrage', 'Normal', 'Physical', 20, 15, 85, True, True, 0, 'Normal', 'Barrage - Physical Normal move.'),
            (141, 'Leech Life', 'Bug', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Leech Life - Physical Bug move.'),
            (142, 'Lovely Kiss', 'Normal', 'Status', 10, None, 75, False, False, 0, 'Normal', 'Lovely Kiss - Status Normal move.'),
            (143, 'Sky Attack', 'Flying', 'Physical', 5, 140, 90, True, True, 0, 'Normal', 'Sky Attack - Physical Flying move.'),
            (144, 'Transform', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Transform - Status Normal move.'),
            (145, 'Bubble', 'Water', 'Special', 30, 40, 100, True, False, 0, 'Normal', 'Bubble - Special Water move.'),
            (146, 'Dizzy Punch', 'Normal', 'Physical', 10, 70, 100, True, True, 0, 'Normal', 'Dizzy Punch - Physical Normal move.'),
            (147, 'Spore', 'Grass', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Spore - Status Grass move.'),
            (148, 'Flash', 'Normal', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Flash - Status Normal move.'),
            (149, 'Psywave', 'Psychic', 'Special', 15, None, 100, False, False, 0, 'Normal', 'Psywave - Special Psychic move.'),
            (150, 'Splash', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Splash - Status Normal move.'),
            (151, 'Acid Armor', 'Poison', 'Status', 20, None, None, False, False, 0, 'Normal', 'Acid Armor - Status Poison move.'),
            (152, 'Crabhammer', 'Water', 'Physical', 10, 100, 90, True, True, 0, 'Normal', 'Crabhammer - Physical Water move.'),
            (153, 'Explosion', 'Normal', 'Physical', 5, 250, 100, True, True, 0, 'All_Adjacent', 'Explosion - Physical Normal move.'),
            (154, 'Fury Swipes', 'Normal', 'Physical', 15, 18, 80, True, True, 0, 'Normal', 'Fury Swipes - Physical Normal move.'),
            (155, 'Bonemerang', 'Ground', 'Physical', 10, 50, 90, True, True, 0, 'Normal', 'Bonemerang - Physical Ground move.'),
            (156, 'Rest', 'Psychic', 'Status', 5, None, None, False, False, 0, 'Self', 'Rest - Status Psychic move.'),
            (157, 'Rock Slide', 'Rock', 'Physical', 10, 75, 90, True, True, 0, 'All_Adjacent_Foes', 'Rock Slide - Physical Rock move.'),
            (158, 'Hyper Fang', 'Normal', 'Physical', 15, 80, 90, True, True, 0, 'Normal', 'Hyper Fang - Physical Normal move.'),
            (159, 'Sharpen', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Sharpen - Status Normal move.'),
            (160, 'Conversion', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Conversion - Status Normal move.'),
            (161, 'Tri Attack', 'Normal', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Tri Attack - Special Normal move.'),
            (162, 'Super Fang', 'Normal', 'Physical', 10, None, 90, False, True, 0, 'Normal', 'Super Fang - Physical Normal move.'),
            (163, 'Slash', 'Normal', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'Slash - Physical Normal move.'),
            (164, 'Substitute', 'Normal', 'Status', 10, None, None, False, False, 0, 'Self', 'Substitute - Status Normal move.'),
            (165, 'Struggle', 'Normal', 'Physical', 1, 50, None, True, True, 0, 'Normal', 'Struggle - Physical Normal move.'),
            (166, 'Sketch', 'Normal', 'Status', 1, None, None, False, False, 0, 'Normal', 'Sketch - Status Normal move.'),
            (167, 'Triple Kick', 'Fighting', 'Physical', 10, 10, 90, True, True, 0, 'Normal', 'Triple Kick - Physical Fighting move.'),
            (168, 'Thief', 'Dark', 'Physical', 25, 60, 100, True, True, 0, 'Normal', 'Thief - Physical Dark move.'),
            (169, 'Spider Web', 'Bug', 'Status', 10, None, None, False, False, 0, 'Normal', 'Spider Web - Status Bug move.'),
            (170, 'Mind Reader', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Mind Reader - Status Normal move.'),
            (171, 'Nightmare', 'Ghost', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Nightmare - Status Ghost move.'),
            (172, 'Flame Wheel', 'Fire', 'Physical', 25, 60, 100, True, True, 0, 'Normal', 'Flame Wheel - Physical Fire move.'),
            (173, 'Snore', 'Normal', 'Special', 15, 50, 100, True, False, 0, 'Normal', 'Snore - Special Normal move.'),
            (174, 'Curse', 'Ghost', 'Status', 10, None, None, False, False, 0, 'Normal', 'Curse - Status Ghost move.'),
            (175, 'Flail', 'Normal', 'Physical', 15, None, 100, False, True, 0, 'Normal', 'Flail - Physical Normal move.'),
            (176, 'Conversion 2', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Conversion 2 - Status Normal move.'),
            (177, 'Aeroblast', 'Flying', 'Special', 5, 100, 95, True, False, 0, 'Normal', 'Aeroblast - Special Flying move.'),
            (178, 'Cotton Spore', 'Grass', 'Status', 40, None, 100, False, False, 0, 'Normal', 'Cotton Spore - Status Grass move.'),
            (179, 'Reversal', 'Fighting', 'Physical', 15, None, 100, False, True, 0, 'Normal', 'Reversal - Physical Fighting move.'),
            (180, 'Spite', 'Ghost', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Spite - Status Ghost move.'),
            (181, 'Powder Snow', 'Ice', 'Special', 25, 40, 100, True, False, 0, 'Normal', 'Powder Snow - Special Ice move.'),
            (182, 'Protect', 'Normal', 'Status', 10, None, None, False, False, 4, 'Normal', 'Protect - Status Normal move.'),
            (183, 'Mach Punch', 'Fighting', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'Mach Punch - Physical Fighting move.'),
            (184, 'Scary Face', 'Normal', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Scary Face - Status Normal move.'),
            (185, 'Feint Attack', 'Dark', 'Physical', 20, 60, None, True, True, 0, 'Normal', 'Feint Attack - Physical Dark move.'),
            (186, 'Sweet Kiss', 'Fairy', 'Status', 10, None, 75, False, False, 0, 'Normal', 'Sweet Kiss - Status Fairy move.'),
            (187, 'Belly Drum', 'Normal', 'Status', 10, None, None, False, False, 0, 'Self', 'Belly Drum - Status Normal move.'),
            (188, 'Sludge Bomb', 'Poison', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Sludge Bomb - Special Poison move.'),
            (189, 'Mud-Slap', 'Ground', 'Special', 10, 20, 100, True, False, 0, 'Normal', 'Mud-Slap - Special Ground move.'),
            (190, 'Octazooka', 'Water', 'Special', 10, 65, 85, True, False, 0, 'Normal', 'Octazooka - Special Water move.'),
            (191, 'Spikes', 'Ground', 'Status', 20, None, None, False, False, 0, 'Opponents_Field', 'Spikes - Status Ground move.'),
            (192, 'Zap Cannon', 'Electric', 'Special', 5, 120, 50, True, False, 0, 'Normal', 'Zap Cannon - Special Electric move.'),
            (193, 'Foresight', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Foresight - Status Normal move.'),
            (194, 'Destiny Bond', 'Ghost', 'Status', 5, None, None, False, False, 0, 'Normal', 'Destiny Bond - Status Ghost move.'),
            (195, 'Perish Song', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Perish Song - Status Normal move.'),
            (196, 'Icy Wind', 'Ice', 'Special', 15, 55, 95, True, False, 0, 'All_Adjacent_Foes', 'Icy Wind - Special Ice move.'),
            (197, 'Detect', 'Fighting', 'Status', 5, None, None, False, False, 4, 'Normal', 'Detect - Status Fighting move.'),
            (198, 'Bone Rush', 'Ground', 'Physical', 10, 25, 90, True, True, 0, 'Normal', 'Bone Rush - Physical Ground move.'),
            (199, 'Lock-On', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Lock-On - Status Normal move.'),
            (200, 'Outrage', 'Dragon', 'Physical', 10, 120, 100, True, True, 0, 'Random_Opponent', 'Outrage - Physical Dragon move.'),
            (201, 'Sandstorm', 'Rock', 'Status', 10, None, None, False, False, 0, 'Field', 'Sandstorm - Status Rock move.'),
            (202, 'Giga Drain', 'Grass', 'Special', 10, 75, 100, True, False, 0, 'Normal', 'Giga Drain - Special Grass move.'),
            (203, 'Endure', 'Normal', 'Status', 10, None, None, False, False, 4, 'Normal', 'Endure - Status Normal move.'),
            (204, 'Charm', 'Fairy', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Charm - Status Fairy move.'),
            (205, 'Rollout', 'Rock', 'Physical', 20, 30, 90, True, True, 0, 'Normal', 'Rollout - Physical Rock move.'),
            (206, 'False Swipe', 'Normal', 'Physical', 40, 40, 100, True, True, 0, 'Normal', 'False Swipe - Physical Normal move.'),
            (207, 'Swagger', 'Normal', 'Status', 15, None, 85, False, False, 0, 'Normal', 'Swagger - Status Normal move.'),
            (208, 'Milk Drink', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Milk Drink - Status Normal move.'),
            (209, 'Spark', 'Electric', 'Physical', 20, 65, 100, True, True, 0, 'Normal', 'Spark - Physical Electric move.'),
            (210, 'Fury Cutter', 'Bug', 'Physical', 20, 40, 95, True, True, 0, 'Normal', 'Fury Cutter - Physical Bug move.'),
            (211, 'Steel Wing', 'Steel', 'Physical', 25, 70, 90, True, True, 0, 'Normal', 'Steel Wing - Physical Steel move.'),
            (212, 'Mean Look', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Mean Look - Status Normal move.'),
            (213, 'Attract', 'Normal', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Attract - Status Normal move.'),
            (214, 'Sleep Talk', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Sleep Talk - Status Normal move.'),
            (215, 'Heal Bell', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Heal Bell - Status Normal move.'),
            (216, 'Return', 'Normal', 'Physical', 20, None, 100, False, True, 0, 'Normal', 'Return - Physical Normal move.'),
            (217, 'Present', 'Normal', 'Physical', 15, None, 90, False, True, 0, 'Normal', 'Present - Physical Normal move.'),
            (218, 'Frustration', 'Normal', 'Physical', 20, None, 100, False, True, 0, 'Normal', 'Frustration - Physical Normal move.'),
            (219, 'Safeguard', 'Normal', 'Status', 25, None, None, False, False, 0, 'UserSide', 'Safeguard - Status Normal move.'),
            (220, 'Pain Split', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Pain Split - Status Normal move.'),
            (221, 'Sacred Fire', 'Fire', 'Physical', 5, 100, 95, True, True, 0, 'Normal', 'Sacred Fire - Physical Fire move.'),
            (222, 'Magnitude', 'Ground', 'Physical', 30, None, 100, False, True, 0, 'All_Adjacent', 'Magnitude - Physical Ground move.'),
            (223, 'Dynamic Punch', 'Fighting', 'Physical', 5, 100, 50, True, True, 0, 'Normal', 'Dynamic Punch - Physical Fighting move.'),
            (224, 'Megahorn', 'Bug', 'Physical', 10, 120, 85, True, True, 0, 'Normal', 'Megahorn - Physical Bug move.'),
            (225, 'Dragon Breath', 'Dragon', 'Special', 20, 60, 100, True, False, 0, 'Normal', 'Dragon Breath - Special Dragon move.'),
            (226, 'Baton Pass', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Baton Pass - Status Normal move.'),
            (227, 'Encore', 'Normal', 'Status', 5, None, 100, False, False, 0, 'Normal', 'Encore - Status Normal move.'),
            (228, 'Pursuit', 'Dark', 'Physical', 20, 40, 100, True, True, 0, 'Normal', 'Pursuit - Physical Dark move.'),
            (229, 'Rapid Spin', 'Normal', 'Physical', 40, 50, 100, True, True, 0, 'Normal', 'Rapid Spin - Physical Normal move.'),
            (230, 'Sweet Scent', 'Normal', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Sweet Scent - Status Normal move.'),
            (231, 'Iron Tail', 'Steel', 'Physical', 15, 100, 75, True, True, 0, 'Normal', 'Iron Tail - Physical Steel move.'),
            (232, 'Metal Claw', 'Steel', 'Physical', 35, 50, 95, True, True, 0, 'Normal', 'Metal Claw - Physical Steel move.'),
            (233, 'Vital Throw', 'Fighting', 'Physical', 10, 70, None, True, True, -1, 'Normal', 'Vital Throw - Physical Fighting move.'),
            (234, 'Morning Sun', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Morning Sun - Status Normal move.'),
            (235, 'Synthesis', 'Grass', 'Status', 5, None, None, False, False, 0, 'Normal', 'Synthesis - Status Grass move.'),
            (236, 'Moonlight', 'Fairy', 'Status', 5, None, None, False, False, 0, 'Normal', 'Moonlight - Status Fairy move.'),
            (237, 'Hidden Power', 'Normal', 'Special', 15, 60, 100, True, False, 0, 'Normal', 'Hidden Power - Special Normal move.'),
            (238, 'Cross Chop', 'Fighting', 'Physical', 5, 100, 80, True, True, 0, 'Normal', 'Cross Chop - Physical Fighting move.'),
            (239, 'Twister', 'Dragon', 'Special', 20, 40, 100, True, False, 0, 'Normal', 'Twister - Special Dragon move.'),
            (240, 'Rain Dance', 'Water', 'Status', 5, None, None, False, False, 0, 'Field', 'Rain Dance - Status Water move.'),
            (241, 'Sunny Day', 'Fire', 'Status', 5, None, None, False, False, 0, 'Field', 'Sunny Day - Status Fire move.'),
            (242, 'Crunch', 'Dark', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Crunch - Physical Dark move.'),
            (243, 'Mirror Coat', 'Psychic', 'Special', 20, None, 100, False, False, -5, 'Normal', 'Mirror Coat - Special Psychic move.'),
            (244, 'Psych Up', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Psych Up - Status Normal move.'),
            (245, 'Extreme Speed', 'Normal', 'Physical', 5, 80, 100, True, True, 1, 'Normal', 'Extreme Speed - Physical Normal move.'),
            (246, 'Ancient Power', 'Rock', 'Special', 5, 60, 100, True, False, 0, 'Normal', 'Ancient Power - Special Rock move.'),
            (247, 'Shadow Ball', 'Ghost', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'Shadow Ball - Special Ghost move.'),
            (248, 'Future Sight', 'Psychic', 'Special', 10, 120, 100, True, False, 0, 'Normal', 'Future Sight - Special Psychic move.'),
            (249, 'Rock Smash', 'Fighting', 'Physical', 15, 40, 100, True, True, 0, 'Normal', 'Rock Smash - Physical Fighting move.'),
            (250, 'Whirlpool', 'Water', 'Special', 15, 35, 85, True, False, 0, 'Normal', 'Whirlpool - Special Water move.'),
            (251, 'Beat Up', 'Dark', 'Physical', 10, None, 100, False, True, 0, 'Normal', 'Beat Up - Physical Dark move.'),
            (252, 'Fake Out', 'Normal', 'Physical', 10, 40, 100, True, True, 1, 'Normal', 'Fake Out - Physical Normal move.'),
            (253, 'Uproar', 'Normal', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Uproar - Special Normal move.'),
            (254, 'Stockpile', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Stockpile - Status Normal move.'),
            (255, 'Spit Up', 'Normal', 'Special', 10, None, 100, False, False, 0, 'Normal', 'Spit Up - Special Normal move.'),
            (256, 'Swallow', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Swallow - Status Normal move.'),
            (257, 'Heat Wave', 'Fire', 'Special', 10, 95, 90, True, False, 0, 'All_Adjacent_Foes', 'Heat Wave - Special Fire move.'),
            (258, 'Hail', 'Ice', 'Status', 10, None, None, False, False, 0, 'Field', 'Hail - Status Ice move.'),
            (259, 'Torment', 'Dark', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Torment - Status Dark move.'),
            (260, 'Flatter', 'Dark', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Flatter - Status Dark move.'),
            (261, 'Will-O-Wisp', 'Fire', 'Status', 15, None, 85, False, False, 0, 'Normal', 'Will-O-Wisp - Status Fire move.'),
            (262, 'Memento', 'Dark', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Memento - Status Dark move.'),
            (263, 'Facade', 'Normal', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'Facade - Physical Normal move.'),
            (264, 'Focus Punch', 'Fighting', 'Physical', 20, 150, 100, True, True, 0, 'Normal', 'Focus Punch - Physical Fighting move.'),
            (265, 'Smelling Salts', 'Normal', 'Physical', 10, 70, 100, True, True, 0, 'Normal', 'Smelling Salts - Physical Normal move.'),
            (266, 'Follow Me', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Follow Me - Status Normal move.'),
            (267, 'Nature Power', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Nature Power - Status Normal move.'),
            (268, 'Charge', 'Electric', 'Status', 20, None, None, False, False, 0, 'Normal', 'Charge - Status Electric move.'),
            (269, 'Taunt', 'Dark', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Taunt - Status Dark move.'),
            (270, 'Helping Hand', 'Normal', 'Status', 20, None, None, False, False, 5, 'Normal', 'Helping Hand - Status Normal move.'),
            (271, 'Trick', 'Psychic', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Trick - Status Psychic move.'),
            (272, 'Role Play', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Role Play - Status Psychic move.'),
            (273, 'Wish', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Wish - Status Normal move.'),
            (274, 'Assist', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Assist - Status Normal move.'),
            (275, 'Ingrain', 'Grass', 'Status', 20, None, None, False, False, 0, 'Normal', 'Ingrain - Status Grass move.'),
            (276, 'Superpower', 'Fighting', 'Physical', 5, 120, 100, True, True, 0, 'Normal', 'Superpower - Physical Fighting move.'),
            (277, 'Magic Coat', 'Psychic', 'Status', 15, None, None, False, False, 0, 'Normal', 'Magic Coat - Status Psychic move.'),
            (278, 'Recycle', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Recycle - Status Normal move.'),
            (279, 'Revenge', 'Fighting', 'Physical', 10, 60, 100, True, True, -4, 'Normal', 'Revenge - Physical Fighting move.'),
            (280, 'Brick Break', 'Fighting', 'Physical', 15, 75, 100, True, True, 0, 'Normal', 'Brick Break - Physical Fighting move.'),
            (281, 'Yawn', 'Normal', 'Status', 10, None, None, False, False, 0, 'Normal', 'Yawn - Status Normal move.'),
            (282, 'Knock Off', 'Dark', 'Physical', 20, 65, 100, True, True, 0, 'Normal', 'Knock Off - Physical Dark move.'),
            (283, 'Endeavor', 'Normal', 'Physical', 5, None, 100, False, True, 0, 'Normal', 'Endeavor - Physical Normal move.'),
            (284, 'Eruption', 'Fire', 'Special', 5, 150, 100, True, False, 0, 'All_Adjacent_Foes', 'Eruption - Special Fire move.'),
            (285, 'Skill Swap', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Skill Swap - Status Psychic move.'),
            (286, 'Imprison', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Imprison - Status Psychic move.'),
            (287, 'Refresh', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Refresh - Status Normal move.'),
            (288, 'Grudge', 'Ghost', 'Status', 5, None, None, False, False, 0, 'Normal', 'Grudge - Status Ghost move.'),
            (289, 'Snatch', 'Dark', 'Status', 10, None, None, False, False, 0, 'Normal', 'Snatch - Status Dark move.'),
            (290, 'Secret Power', 'Normal', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'Secret Power - Physical Normal move.'),
            (291, 'Dive', 'Water', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Dive - Physical Water move.'),
            (292, 'Arm Thrust', 'Fighting', 'Physical', 20, 15, 100, True, True, 0, 'Normal', 'Arm Thrust - Physical Fighting move.'),
            (293, 'Camouflage', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Camouflage - Status Normal move.'),
            (294, 'Tail Glow', 'Bug', 'Status', 20, None, None, False, False, 0, 'Self', 'Tail Glow - Status Bug move.'),
            (295, 'Luster Purge', 'Psychic', 'Special', 5, 95, 100, True, False, 0, 'Normal', 'Luster Purge - Special Psychic move.'),
            (296, 'Mist Ball', 'Psychic', 'Special', 5, 95, 100, True, False, 0, 'Normal', 'Mist Ball - Special Psychic move.'),
            (297, 'Feather Dance', 'Flying', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Feather Dance - Status Flying move.'),
            (298, 'Teeter Dance', 'Normal', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Teeter Dance - Status Normal move.'),
            (299, 'Blaze Kick', 'Fire', 'Physical', 10, 85, 90, True, True, 0, 'Normal', 'Blaze Kick - Physical Fire move.'),
            (300, 'Mud Sport', 'Ground', 'Status', 15, None, None, False, False, 0, 'Normal', 'Mud Sport - Status Ground move.'),
            (301, 'Ice Ball', 'Ice', 'Physical', 20, 30, 90, True, True, 0, 'Normal', 'Ice Ball - Physical Ice move.'),
            (302, 'Needle Arm', 'Grass', 'Physical', 15, 60, 100, True, True, 0, 'Normal', 'Needle Arm - Physical Grass move.'),
            (303, 'Slack Off', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Slack Off - Status Normal move.'),
            (304, 'Hyper Voice', 'Normal', 'Special', 10, 90, 100, True, False, 0, 'All_Adjacent_Foes', 'Hyper Voice - Special Normal move.'),
            (305, 'Poison Fang', 'Poison', 'Physical', 15, 50, 100, True, True, 0, 'Normal', 'Poison Fang - Physical Poison move.'),
            (306, 'Crush Claw', 'Normal', 'Physical', 10, 75, 95, True, True, 0, 'Normal', 'Crush Claw - Physical Normal move.'),
            (307, 'Blast Burn', 'Fire', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'Blast Burn - Special Fire move.'),
            (308, 'Hydro Cannon', 'Water', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'Hydro Cannon - Special Water move.'),
            (309, 'Meteor Mash', 'Steel', 'Physical', 10, 90, 90, True, True, 0, 'Normal', 'Meteor Mash - Physical Steel move.'),
            (310, 'Astonish', 'Ghost', 'Physical', 15, 30, 100, True, True, 0, 'Normal', 'Astonish - Physical Ghost move.'),
            (311, 'Weather Ball', 'Normal', 'Special', 10, 50, 100, True, False, 0, 'Normal', 'Weather Ball - Special Normal move.'),
            (312, 'Aromatherapy', 'Grass', 'Status', 5, None, None, False, False, 0, 'Normal', 'Aromatherapy - Status Grass move.'),
            (313, 'Fake Tears', 'Dark', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Fake Tears - Status Dark move.'),
            (314, 'Air Cutter', 'Flying', 'Special', 25, 60, 95, True, False, 0, 'Normal', 'Air Cutter - Special Flying move.'),
            (315, 'Overheat', 'Fire', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Overheat - Special Fire move.'),
            (316, 'Odor Sleuth', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Odor Sleuth - Status Normal move.'),
            (317, 'Rock Tomb', 'Rock', 'Physical', 15, 60, 95, True, True, 0, 'Normal', 'Rock Tomb - Physical Rock move.'),
            (318, 'Silver Wind', 'Bug', 'Special', 5, 60, 100, True, False, 0, 'Normal', 'Silver Wind - Special Bug move.'),
            (319, 'Metal Sound', 'Steel', 'Status', 40, None, 85, False, False, 0, 'Normal', 'Metal Sound - Status Steel move.'),
            (320, 'Grass Whistle', 'Grass', 'Status', 15, None, 55, False, False, 0, 'Normal', 'Grass Whistle - Status Grass move.'),
            (321, 'Tickle', 'Normal', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Tickle - Status Normal move.'),
            (322, 'Cosmic Power', 'Psychic', 'Status', 20, None, None, False, False, 0, 'Normal', 'Cosmic Power - Status Psychic move.'),
            (323, 'Water Spout', 'Water', 'Special', 5, 150, 100, True, False, 0, 'All_Adjacent_Foes', 'Water Spout - Special Water move.'),
            (324, 'Signal Beam', 'Bug', 'Special', 15, 75, 100, True, False, 0, 'Normal', 'Signal Beam - Special Bug move.'),
            (325, 'Shadow Punch', 'Ghost', 'Physical', 20, 60, None, True, True, 0, 'Normal', 'Shadow Punch - Physical Ghost move.'),
            (326, 'Extrasensory', 'Psychic', 'Special', 20, 80, 100, True, False, 0, 'Normal', 'Extrasensory - Special Psychic move.'),
            (327, 'Sky Uppercut', 'Fighting', 'Physical', 15, 85, 90, True, True, 0, 'Normal', 'Sky Uppercut - Physical Fighting move.'),
            (328, 'Sand Tomb', 'Ground', 'Physical', 15, 35, 85, True, True, 0, 'Normal', 'Sand Tomb - Physical Ground move.'),
            (329, 'Sheer Cold', 'Ice', 'Special', 5, None, 30, False, False, 0, 'Normal', 'Sheer Cold - Special Ice move.'),
            (330, 'Muddy Water', 'Water', 'Special', 10, 90, 85, True, False, 0, 'All_Adjacent_Foes', 'Muddy Water - Special Water move.'),
            (331, 'Bullet Seed', 'Grass', 'Physical', 30, 25, 100, True, True, 0, 'Normal', 'Bullet Seed - Physical Grass move.'),
            (332, 'Aerial Ace', 'Flying', 'Physical', 20, 60, None, True, True, 0, 'Normal', 'Aerial Ace - Physical Flying move.'),
            (333, 'Icicle Spear', 'Ice', 'Physical', 30, 25, 100, True, True, 0, 'Normal', 'Icicle Spear - Physical Ice move.'),
            (334, 'Iron Defense', 'Steel', 'Status', 15, None, None, False, False, 0, 'Self', 'Iron Defense - Status Steel move.'),
            (335, 'Block', 'Normal', 'Status', 5, None, None, False, False, 0, 'Normal', 'Block - Status Normal move.'),
            (336, 'Howl', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Howl - Status Normal move.'),
            (337, 'Dragon Claw', 'Dragon', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Dragon Claw - Physical Dragon move.'),
            (338, 'Frenzy Plant', 'Grass', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'Frenzy Plant - Special Grass move.'),
            (339, 'Bulk Up', 'Fighting', 'Status', 20, None, None, False, False, 0, 'Self', 'Bulk Up - Status Fighting move.'),
            (340, 'Bounce', 'Flying', 'Physical', 5, 85, 85, True, True, 0, 'Normal', 'Bounce - Physical Flying move.'),
            (341, 'Mud Shot', 'Ground', 'Special', 15, 55, 95, True, False, 0, 'Normal', 'Mud Shot - Special Ground move.'),
            (342, 'Poison Tail', 'Poison', 'Physical', 25, 50, 100, True, True, 0, 'Normal', 'Poison Tail - Physical Poison move.'),
            (343, 'Covet', 'Normal', 'Physical', 25, 60, 100, True, True, 0, 'Normal', 'Covet - Physical Normal move.'),
            (344, 'Volt Tackle', 'Electric', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'Volt Tackle - Physical Electric move.'),
            (345, 'Magical Leaf', 'Grass', 'Special', 20, 60, None, True, False, 0, 'Normal', 'Magical Leaf - Special Grass move.'),
            (346, 'Water Sport', 'Water', 'Status', 15, None, None, False, False, 0, 'Normal', 'Water Sport - Status Water move.'),
            (347, 'Calm Mind', 'Psychic', 'Status', 20, None, None, False, False, 0, 'Self', 'Calm Mind - Status Psychic move.'),
            (348, 'Leaf Blade', 'Grass', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'Leaf Blade - Physical Grass move.'),
            (349, 'Dragon Dance', 'Dragon', 'Status', 20, None, None, False, False, 0, 'Normal', 'Dragon Dance - Status Dragon move.'),
            (350, 'Rock Blast', 'Rock', 'Physical', 10, 25, 90, True, True, 0, 'Normal', 'Rock Blast - Physical Rock move.'),
            (351, 'Shock Wave', 'Electric', 'Special', 20, 60, None, True, False, 0, 'Normal', 'Shock Wave - Special Electric move.'),
            (352, 'Water Pulse', 'Water', 'Special', 20, 60, 100, True, False, 0, 'Normal', 'Water Pulse - Special Water move.'),
            (353, 'Doom Desire', 'Steel', 'Special', 5, 140, 100, True, False, 0, 'Normal', 'Doom Desire - Special Steel move.'),
            (354, 'Psycho Boost', 'Psychic', 'Special', 5, 140, 90, True, False, 0, 'Normal', 'Psycho Boost - Special Psychic move.'),
            (355, 'Roost', 'Flying', 'Status', 5, None, None, False, False, 0, 'Normal', 'Roost - Status Flying move.'),
            (356, 'Gravity', 'Psychic', 'Status', 5, None, None, False, False, 0, 'Normal', 'Gravity - Status Psychic move.'),
            (357, 'Miracle Eye', 'Psychic', 'Status', 40, None, None, False, False, 0, 'Normal', 'Miracle Eye - Status Psychic move.'),
            (358, 'Wake-Up Slap', 'Fighting', 'Physical', 10, 70, 100, True, True, 0, 'Normal', 'Wake-Up Slap - Physical Fighting move.'),
            (359, 'Hammer Arm', 'Fighting', 'Physical', 10, 100, 90, True, True, 0, 'Normal', 'Hammer Arm - Physical Fighting move.'),
            (360, 'Gyro Ball', 'Steel', 'Physical', 5, None, 100, False, True, 0, 'Normal', 'Gyro Ball - Physical Steel move.'),
            (361, 'Healing Wish', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Healing Wish - Status Psychic move.'),
            (362, 'Brine', 'Water', 'Special', 10, 65, 100, True, False, 0, 'Normal', 'Brine - Special Water move.'),
            (363, 'Natural Gift', 'Normal', 'Physical', 15, None, 100, False, True, 0, 'Normal', 'Natural Gift - Physical Normal move.'),
            (364, 'Feint', 'Normal', 'Physical', 10, 30, 100, True, True, 0, 'Normal', 'Feint - Physical Normal move.'),
            (365, 'Pluck', 'Flying', 'Physical', 20, 60, 100, True, True, 0, 'Normal', 'Pluck - Physical Flying move.'),
            (366, 'Tailwind', 'Flying', 'Status', 15, None, None, False, False, 0, 'UserSide', 'Tailwind - Status Flying move.'),
            (367, 'Acupressure', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Acupressure - Status Normal move.'),
            (368, 'Metal Burst', 'Steel', 'Physical', 10, None, 100, False, True, 0, 'Normal', 'Metal Burst - Physical Steel move.'),
            (369, 'U-turn', 'Bug', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'U-turn - Physical Bug move.'),
            (370, 'Close Combat', 'Fighting', 'Physical', 5, 120, 100, True, True, 0, 'Normal', 'Close Combat - Physical Fighting move.'),
            (371, 'Payback', 'Dark', 'Physical', 10, 50, 100, True, True, 0, 'Normal', 'Payback - Physical Dark move.'),
            (372, 'Assurance', 'Dark', 'Physical', 10, 60, 100, True, True, 0, 'Normal', 'Assurance - Physical Dark move.'),
            (373, 'Embargo', 'Dark', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Embargo - Status Dark move.'),
            (374, 'Fling', 'Dark', 'Physical', 10, None, 100, False, True, 0, 'Normal', 'Fling - Physical Dark move.'),
            (375, 'Psycho Shift', 'Psychic', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Psycho Shift - Status Psychic move.'),
            (376, 'Trump Card', 'Normal', 'Special', 5, None, None, False, False, 0, 'Normal', 'Trump Card - Special Normal move.'),
            (377, 'Heal Block', 'Psychic', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Heal Block - Status Psychic move.'),
            (378, 'Wring Out', 'Normal', 'Special', 5, None, 100, False, False, 0, 'Normal', 'Wring Out - Special Normal move.'),
            (379, 'Power Trick', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Power Trick - Status Psychic move.'),
            (380, 'Gastro Acid', 'Poison', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Gastro Acid - Status Poison move.'),
            (381, 'Lucky Chant', 'Normal', 'Status', 30, None, None, False, False, 0, 'UserSide', 'Lucky Chant - Status Normal move.'),
            (382, 'Me First', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Me First - Status Normal move.'),
            (383, 'Copycat', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Copycat - Status Normal move.'),
            (384, 'Power Swap', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Power Swap - Status Psychic move.'),
            (385, 'Guard Swap', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Guard Swap - Status Psychic move.'),
            (386, 'Punishment', 'Dark', 'Physical', 5, None, 100, False, True, 0, 'Normal', 'Punishment - Physical Dark move.'),
            (387, 'Last Resort', 'Normal', 'Physical', 5, 140, 100, True, True, 0, 'Normal', 'Last Resort - Physical Normal move.'),
            (388, 'Worry Seed', 'Grass', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Worry Seed - Status Grass move.'),
            (389, 'Sucker Punch', 'Dark', 'Physical', 5, 70, 100, True, True, 1, 'Normal', 'Sucker Punch - Physical Dark move.'),
            (390, 'Toxic Spikes', 'Poison', 'Status', 20, None, None, False, False, 0, 'Opponents_Field', 'Toxic Spikes - Status Poison move.'),
            (391, 'Heart Swap', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Heart Swap - Status Psychic move.'),
            (392, 'Aqua Ring', 'Water', 'Status', 20, None, None, False, False, 0, 'Normal', 'Aqua Ring - Status Water move.'),
            (393, 'Magnet Rise', 'Electric', 'Status', 10, None, None, False, False, 0, 'Normal', 'Magnet Rise - Status Electric move.'),
            (394, 'Flare Blitz', 'Fire', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'Flare Blitz - Physical Fire move.'),
            (395, 'Force Palm', 'Fighting', 'Physical', 10, 60, 100, True, True, 0, 'Normal', 'Force Palm - Physical Fighting move.'),
            (396, 'Aura Sphere', 'Fighting', 'Special', 20, 80, None, True, False, 0, 'Normal', 'Aura Sphere - Special Fighting move.'),
            (397, 'Rock Polish', 'Rock', 'Status', 20, None, None, False, False, 0, 'Self', 'Rock Polish - Status Rock move.'),
            (398, 'Poison Jab', 'Poison', 'Physical', 20, 80, 100, True, True, 0, 'Normal', 'Poison Jab - Physical Poison move.'),
            (399, 'Dark Pulse', 'Dark', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'Dark Pulse - Special Dark move.'),
            (400, 'Night Slash', 'Dark', 'Physical', 15, 70, 100, True, True, 0, 'Normal', 'Night Slash - Physical Dark move.'),
            (401, 'Aqua Tail', 'Water', 'Physical', 10, 90, 90, True, True, 0, 'Normal', 'Aqua Tail - Physical Water move.'),
            (402, 'Seed Bomb', 'Grass', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Seed Bomb - Physical Grass move.'),
            (403, 'Air Slash', 'Flying', 'Special', 15, 75, 95, True, False, 0, 'Normal', 'Air Slash - Special Flying move.'),
            (404, 'X-Scissor', 'Bug', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'X-Scissor - Physical Bug move.'),
            (405, 'Bug Buzz', 'Bug', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Bug Buzz - Special Bug move.'),
            (406, 'Dragon Pulse', 'Dragon', 'Special', 10, 85, 100, True, False, 0, 'Normal', 'Dragon Pulse - Special Dragon move.'),
            (407, 'Dragon Rush', 'Dragon', 'Physical', 10, 100, 75, True, True, 0, 'Normal', 'Dragon Rush - Physical Dragon move.'),
            (408, 'Power Gem', 'Rock', 'Special', 20, 80, 100, True, False, 0, 'Normal', 'Power Gem - Special Rock move.'),
            (409, 'Drain Punch', 'Fighting', 'Physical', 10, 75, 100, True, True, 0, 'Normal', 'Drain Punch - Physical Fighting move.'),
            (410, 'Vacuum Wave', 'Fighting', 'Special', 30, 40, 100, True, False, 0, 'Normal', 'Vacuum Wave - Special Fighting move.'),
            (411, 'Focus Blast', 'Fighting', 'Special', 5, 120, 70, True, False, 0, 'Normal', 'Focus Blast - Special Fighting move.'),
            (412, 'Energy Ball', 'Grass', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Energy Ball - Special Grass move.'),
            (413, 'Brave Bird', 'Flying', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'Brave Bird - Physical Flying move.'),
            (414, 'Earth Power', 'Ground', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Earth Power - Special Ground move.'),
            (415, 'Switcheroo', 'Dark', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Switcheroo - Status Dark move.'),
            (416, 'Giga Impact', 'Normal', 'Physical', 5, 150, 90, True, True, 0, 'Normal', 'Giga Impact - Physical Normal move.'),
            (417, 'Nasty Plot', 'Dark', 'Status', 20, None, None, False, False, 0, 'Self', 'Nasty Plot - Status Dark move.'),
            (418, 'Bullet Punch', 'Steel', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'Bullet Punch - Physical Steel move.'),
            (419, 'Avalanche', 'Ice', 'Physical', 10, 60, 100, True, True, -4, 'Normal', 'Avalanche - Physical Ice move.'),
            (420, 'Ice Shard', 'Ice', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'Ice Shard - Physical Ice move.'),
            (421, 'Shadow Claw', 'Ghost', 'Physical', 15, 70, 100, True, True, 0, 'Normal', 'Shadow Claw - Physical Ghost move.'),
            (422, 'Thunder Fang', 'Electric', 'Physical', 15, 65, 95, True, True, 0, 'Normal', 'Thunder Fang - Physical Electric move.'),
            (423, 'Ice Fang', 'Ice', 'Physical', 15, 65, 95, True, True, 0, 'Normal', 'Ice Fang - Physical Ice move.'),
            (424, 'Fire Fang', 'Fire', 'Physical', 15, 65, 95, True, True, 0, 'Normal', 'Fire Fang - Physical Fire move.'),
            (425, 'Shadow Sneak', 'Ghost', 'Physical', 30, 40, 100, True, True, 1, 'Normal', 'Shadow Sneak - Physical Ghost move.'),
            (426, 'Mud Bomb', 'Ground', 'Special', 10, 65, 85, True, False, 0, 'Normal', 'Mud Bomb - Special Ground move.'),
            (427, 'Psycho Cut', 'Psychic', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'Psycho Cut - Physical Psychic move.'),
            (428, 'Zen Headbutt', 'Psychic', 'Physical', 15, 80, 90, True, True, 0, 'Normal', 'Zen Headbutt - Physical Psychic move.'),
            (429, 'Mirror Shot', 'Steel', 'Special', 10, 65, 85, True, False, 0, 'Normal', 'Mirror Shot - Special Steel move.'),
            (430, 'Flash Cannon', 'Steel', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Flash Cannon - Special Steel move.'),
            (431, 'Rock Climb', 'Normal', 'Physical', 20, 90, 85, True, True, 0, 'Normal', 'Rock Climb - Physical Normal move.'),
            (432, 'Defog', 'Flying', 'Status', 15, None, None, False, False, 0, 'Normal', 'Defog - Status Flying move.'),
            (433, 'Trick Room', 'Psychic', 'Status', 5, None, None, False, False, 0, 'Field', 'Trick Room - Status Psychic move.'),
            (434, 'Draco Meteor', 'Dragon', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Draco Meteor - Special Dragon move.'),
            (435, 'Discharge', 'Electric', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'Discharge - Special Electric move.'),
            (436, 'Lava Plume', 'Fire', 'Special', 15, 80, 100, True, False, 0, 'All_Adjacent', 'Lava Plume - Special Fire move.'),
            (437, 'Leaf Storm', 'Grass', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Leaf Storm - Special Grass move.'),
            (438, 'Power Whip', 'Grass', 'Physical', 10, 120, 85, True, True, 0, 'Normal', 'Power Whip - Physical Grass move.'),
            (439, 'Rock Wrecker', 'Rock', 'Physical', 5, 150, 90, True, True, 0, 'Normal', 'Rock Wrecker - Physical Rock move.'),
            (440, 'Cross Poison', 'Poison', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'Cross Poison - Physical Poison move.'),
            (441, 'Gunk Shot', 'Poison', 'Physical', 5, 120, 80, True, True, 0, 'Normal', 'Gunk Shot - Physical Poison move.'),
            (442, 'Iron Head', 'Steel', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Iron Head - Physical Steel move.'),
            (443, 'Magnet Bomb', 'Steel', 'Physical', 20, 60, None, True, True, 0, 'Normal', 'Magnet Bomb - Physical Steel move.'),
            (444, 'Stone Edge', 'Rock', 'Physical', 5, 100, 80, True, True, 0, 'Normal', 'Stone Edge - Physical Rock move.'),
            (445, 'Captivate', 'Normal', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Captivate - Status Normal move.'),
            (446, 'Stealth Rock', 'Rock', 'Status', 20, None, None, False, False, 0, 'Opponents_Field', 'Stealth Rock - Status Rock move.'),
            (447, 'Grass Knot', 'Grass', 'Special', 20, None, 100, False, False, 0, 'Normal', 'Grass Knot - Special Grass move.'),
            (448, 'Chatter', 'Flying', 'Special', 20, 65, 100, True, False, 0, 'Normal', 'Chatter - Special Flying move.'),
            (449, 'Judgment', 'Normal', 'Special', 10, 100, 100, True, False, 0, 'Normal', 'Judgment - Special Normal move.'),
            (450, 'Bug Bite', 'Bug', 'Physical', 20, 60, 100, True, True, 0, 'Normal', 'Bug Bite - Physical Bug move.'),
            (451, 'Charge Beam', 'Electric', 'Special', 10, 50, 90, True, False, 0, 'Normal', 'Charge Beam - Special Electric move.'),
            (452, 'Wood Hammer', 'Grass', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'Wood Hammer - Physical Grass move.'),
            (453, 'Aqua Jet', 'Water', 'Physical', 20, 40, 100, True, True, 1, 'Normal', 'Aqua Jet - Physical Water move.'),
            (454, 'Attack Order', 'Bug', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'Attack Order - Physical Bug move.'),
            (455, 'Defend Order', 'Bug', 'Status', 10, None, None, False, False, 0, 'Normal', 'Defend Order - Status Bug move.'),
            (456, 'Heal Order', 'Bug', 'Status', 10, None, None, False, False, 0, 'Normal', 'Heal Order - Status Bug move.'),
            (457, 'Head Smash', 'Rock', 'Physical', 5, 150, 80, True, True, 0, 'Normal', 'Head Smash - Physical Rock move.'),
            (458, 'Double Hit', 'Normal', 'Physical', 10, 35, 90, True, True, 0, 'Normal', 'Double Hit - Physical Normal move.'),
            (459, 'Roar of Time', 'Dragon', 'Special', 5, 150, 90, True, False, 0, 'Normal', 'Roar of Time - Special Dragon move.'),
            (460, 'Spacial Rend', 'Dragon', 'Special', 5, 100, 95, True, False, 0, 'Normal', 'Spacial Rend - Special Dragon move.'),
            (461, 'Lunar Dance', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Lunar Dance - Status Psychic move.'),
            (462, 'Crush Grip', 'Normal', 'Physical', 5, None, 100, False, True, 0, 'Normal', 'Crush Grip - Physical Normal move.'),
            (463, 'Magma Storm', 'Fire', 'Special', 5, 100, 75, True, False, 0, 'Normal', 'Magma Storm - Special Fire move.'),
            (464, 'Dark Void', 'Dark', 'Status', 10, None, 50, False, False, 0, 'Normal', 'Dark Void - Status Dark move.'),
            (465, 'Seed Flare', 'Grass', 'Special', 5, 120, 85, True, False, 0, 'Normal', 'Seed Flare - Special Grass move.'),
            (466, 'Ominous Wind', 'Ghost', 'Special', 5, 60, 100, True, False, 0, 'Normal', 'Ominous Wind - Special Ghost move.'),
            (467, 'Shadow Force', 'Ghost', 'Physical', 5, 120, 100, True, True, 0, 'Normal', 'Shadow Force - Physical Ghost move.'),
            (468, 'Hone Claws', 'Dark', 'Status', 15, None, None, False, False, 0, 'Self', 'Hone Claws - Status Dark move.'),
            (469, 'Wide Guard', 'Rock', 'Status', 10, None, None, False, False, 0, 'Normal', 'Wide Guard - Status Rock move.'),
            (470, 'Guard Split', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Guard Split - Status Psychic move.'),
            (471, 'Power Split', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Power Split - Status Psychic move.'),
            (472, 'Wonder Room', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Field', 'Wonder Room - Status Psychic move.'),
            (473, 'Psyshock', 'Psychic', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Psyshock - Special Psychic move.'),
            (474, 'Venoshock', 'Poison', 'Special', 10, 65, 100, True, False, 0, 'Normal', 'Venoshock - Special Poison move.'),
            (475, 'Autotomize', 'Steel', 'Status', 15, None, None, False, False, 0, 'Self', 'Autotomize - Status Steel move.'),
            (476, 'Rage Powder', 'Bug', 'Status', 20, None, None, False, False, 0, 'Normal', 'Rage Powder - Status Bug move.'),
            (477, 'Telekinesis', 'Psychic', 'Status', 15, None, None, False, False, 0, 'Normal', 'Telekinesis - Status Psychic move.'),
            (478, 'Magic Room', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Field', 'Magic Room - Status Psychic move.'),
            (479, 'Smack Down', 'Rock', 'Physical', 15, 50, 100, True, True, 0, 'Normal', 'Smack Down - Physical Rock move.'),
            (480, 'Storm Throw', 'Fighting', 'Physical', 10, 60, 100, True, True, 0, 'Normal', 'Storm Throw - Physical Fighting move.'),
            (481, 'Flame Burst', 'Fire', 'Special', 15, 70, 100, True, False, 0, 'Normal', 'Flame Burst - Special Fire move.'),
            (482, 'Sludge Wave', 'Poison', 'Special', 10, 95, 100, True, False, 0, 'All_Adjacent', 'Sludge Wave - Special Poison move.'),
            (483, 'Quiver Dance', 'Bug', 'Status', 20, None, None, False, False, 0, 'Self', 'Quiver Dance - Status Bug move.'),
            (484, 'Heavy Slam', 'Steel', 'Physical', 10, None, 100, False, True, 0, 'Normal', 'Heavy Slam - Physical Steel move.'),
            (485, 'Synchronoise', 'Psychic', 'Special', 10, 120, 100, True, False, 0, 'Normal', 'Synchronoise - Special Psychic move.'),
            (486, 'Electro Ball', 'Electric', 'Special', 10, None, 100, False, False, 0, 'Normal', 'Electro Ball - Special Electric move.'),
            (487, 'Soak', 'Water', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Soak - Status Water move.'),
            (488, 'Flame Charge', 'Fire', 'Physical', 20, 50, 100, True, True, 0, 'Normal', 'Flame Charge - Physical Fire move.'),
            (489, 'Coil', 'Poison', 'Status', 20, None, None, False, False, 0, 'Self', 'Coil - Status Poison move.'),
            (490, 'Low Sweep', 'Fighting', 'Physical', 20, 65, 100, True, True, 0, 'Normal', 'Low Sweep - Physical Fighting move.'),
            (491, 'Acid Spray', 'Poison', 'Special', 20, 40, 100, True, False, 0, 'Normal', 'Acid Spray - Special Poison move.'),
            (492, 'Foul Play', 'Dark', 'Physical', 15, 95, 100, True, True, 0, 'Normal', 'Foul Play - Physical Dark move.'),
            (493, 'Simple Beam', 'Normal', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Simple Beam - Status Normal move.'),
            (494, 'Entrainment', 'Normal', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Entrainment - Status Normal move.'),
            (495, 'After You', 'Normal', 'Status', 15, None, None, False, False, 0, 'Normal', 'After You - Status Normal move.'),
            (496, 'Round', 'Normal', 'Special', 15, 60, 100, True, False, 0, 'Normal', 'Round - Special Normal move.'),
            (497, 'Echoed Voice', 'Normal', 'Special', 15, 40, 100, True, False, 0, 'Normal', 'Echoed Voice - Special Normal move.'),
            (498, 'Chip Away', 'Normal', 'Physical', 20, 70, 100, True, True, 0, 'Normal', 'Chip Away - Physical Normal move.'),
            (499, 'Clear Smog', 'Poison', 'Special', 15, 50, None, True, False, 0, 'Normal', 'Clear Smog - Special Poison move.'),
            (500, 'Stored Power', 'Psychic', 'Special', 10, 20, 100, True, False, 0, 'Normal', 'Stored Power - Special Psychic move.'),
            (501, 'Quick Guard', 'Fighting', 'Status', 15, None, None, False, False, 0, 'Normal', 'Quick Guard - Status Fighting move.'),
            (502, 'Ally Switch', 'Psychic', 'Status', 15, None, None, False, False, 0, 'Normal', 'Ally Switch - Status Psychic move.'),
            (503, 'Scald', 'Water', 'Special', 15, 80, 100, True, False, 0, 'Normal', 'Scald - Special Water move.'),
            (504, 'Shell Smash', 'Normal', 'Status', 15, None, None, False, False, 0, 'Self', 'Shell Smash - Status Normal move.'),
            (505, 'Heal Pulse', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Heal Pulse - Status Psychic move.'),
            (506, 'Hex', 'Ghost', 'Special', 10, 65, 100, True, False, 0, 'Normal', 'Hex - Special Ghost move.'),
            (507, 'Sky Drop', 'Flying', 'Physical', 10, 60, 100, True, True, 0, 'Normal', 'Sky Drop - Physical Flying move.'),
            (508, 'Shift Gear', 'Steel', 'Status', 10, None, None, False, False, 0, 'Self', 'Shift Gear - Status Steel move.'),
            (509, 'Circle Throw', 'Fighting', 'Physical', 10, 60, 90, True, True, -6, 'Normal', 'Circle Throw - Physical Fighting move.'),
            (510, 'Incinerate', 'Fire', 'Special', 15, 60, 100, True, False, 0, 'Normal', 'Incinerate - Special Fire move.'),
            (511, 'Quash', 'Dark', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Quash - Status Dark move.'),
            (512, 'Acrobatics', 'Flying', 'Physical', 15, 55, 100, True, True, 0, 'Normal', 'Acrobatics - Physical Flying move.'),
            (513, 'Reflect Type', 'Normal', 'Status', 15, None, None, False, False, 0, 'Normal', 'Reflect Type - Status Normal move.'),
            (514, 'Retaliate', 'Normal', 'Physical', 5, 70, 100, True, True, 0, 'Normal', 'Retaliate - Physical Normal move.'),
            (515, 'Final Gambit', 'Fighting', 'Special', 5, None, 100, False, False, 0, 'Normal', 'Final Gambit - Special Fighting move.'),
            (516, 'Bestow', 'Normal', 'Status', 15, None, None, False, False, 0, 'Normal', 'Bestow - Status Normal move.'),
            (517, 'Inferno', 'Fire', 'Special', 5, 100, 50, True, False, 0, 'Normal', 'Inferno - Special Fire move.'),
            (518, 'Water Pledge', 'Water', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Water Pledge - Special Water move.'),
            (519, 'Fire Pledge', 'Fire', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Fire Pledge - Special Fire move.'),
            (520, 'Grass Pledge', 'Grass', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Grass Pledge - Special Grass move.'),
            (521, 'Volt Switch', 'Electric', 'Special', 20, 70, 100, True, False, 0, 'Normal', 'Volt Switch - Special Electric move.'),
            (522, 'Struggle Bug', 'Bug', 'Special', 20, 50, 100, True, False, 0, 'Normal', 'Struggle Bug - Special Bug move.'),
            (523, 'Bulldoze', 'Ground', 'Physical', 20, 60, 100, True, True, 0, 'All_Adjacent', 'Bulldoze - Physical Ground move.'),
            (524, 'Frost Breath', 'Ice', 'Special', 10, 60, 90, True, False, 0, 'Normal', 'Frost Breath - Special Ice move.'),
            (525, 'Dragon Tail', 'Dragon', 'Physical', 10, 60, 90, True, True, -6, 'Normal', 'Dragon Tail - Physical Dragon move.'),
            (526, 'Work Up', 'Normal', 'Status', 30, None, None, False, False, 0, 'Self', 'Work Up - Status Normal move.'),
            (527, 'Electroweb', 'Electric', 'Special', 15, 55, 95, True, False, 0, 'All_Adjacent_Foes', 'Electroweb - Special Electric move.'),
            (528, 'Wild Charge', 'Electric', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'Wild Charge - Physical Electric move.'),
            (529, 'Drill Run', 'Ground', 'Physical', 10, 80, 95, True, True, 0, 'Normal', 'Drill Run - Physical Ground move.'),
            (530, 'Dual Chop', 'Dragon', 'Physical', 15, 40, 90, True, True, 0, 'Normal', 'Dual Chop - Physical Dragon move.'),
            (531, 'Heart Stamp', 'Psychic', 'Physical', 25, 60, 100, True, True, 0, 'Normal', 'Heart Stamp - Physical Psychic move.'),
            (532, 'Horn Leech', 'Grass', 'Physical', 10, 75, 100, True, True, 0, 'Normal', 'Horn Leech - Physical Grass move.'),
            (533, 'Sacred Sword', 'Fighting', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'Sacred Sword - Physical Fighting move.'),
            (534, 'Razor Shell', 'Water', 'Physical', 10, 75, 95, True, True, 0, 'Normal', 'Razor Shell - Physical Water move.'),
            (535, 'Heat Crash', 'Fire', 'Physical', 10, None, 100, False, True, 0, 'Normal', 'Heat Crash - Physical Fire move.'),
            (536, 'Leaf Tornado', 'Grass', 'Special', 10, 65, 90, True, False, 0, 'Normal', 'Leaf Tornado - Special Grass move.'),
            (537, 'Steamroller', 'Bug', 'Physical', 20, 65, 100, True, True, 0, 'Normal', 'Steamroller - Physical Bug move.'),
            (538, 'Cotton Guard', 'Grass', 'Status', 10, None, None, False, False, 0, 'Self', 'Cotton Guard - Status Grass move.'),
            (539, 'Night Daze', 'Dark', 'Special', 10, 85, 95, True, False, 0, 'Normal', 'Night Daze - Special Dark move.'),
            (540, 'Psystrike', 'Psychic', 'Special', 10, 100, 100, True, False, 0, 'Normal', 'Psystrike - Special Psychic move.'),
            (541, 'Tail Slap', 'Normal', 'Physical', 10, 25, 85, True, True, 0, 'Normal', 'Tail Slap - Physical Normal move.'),
            (542, 'Hurricane', 'Flying', 'Special', 10, 110, 70, True, False, 0, 'Normal', 'Hurricane - Special Flying move.'),
            (543, 'Head Charge', 'Normal', 'Physical', 15, 120, 100, True, True, 0, 'Normal', 'Head Charge - Physical Normal move.'),
            (544, 'Gear Grind', 'Steel', 'Physical', 15, 50, 85, True, True, 0, 'Normal', 'Gear Grind - Physical Steel move.'),
            (545, 'Searing Shot', 'Fire', 'Special', 5, 100, 100, True, False, 0, 'All_Adjacent', 'Searing Shot - Special Fire move.'),
            (546, 'Techno Blast', 'Normal', 'Special', 5, 120, 100, True, False, 0, 'Normal', 'Techno Blast - Special Normal move.'),
            (547, 'Relic Song', 'Normal', 'Special', 10, 75, 100, True, False, 0, 'Normal', 'Relic Song - Special Normal move.'),
            (548, 'Secret Sword', 'Fighting', 'Special', 10, 85, 100, True, False, 0, 'Normal', 'Secret Sword - Special Fighting move.'),
            (549, 'Glaciate', 'Ice', 'Special', 10, 65, 95, True, False, 0, 'All_Adjacent_Foes', 'Glaciate - Special Ice move.'),
            (550, 'Bolt Strike', 'Electric', 'Physical', 5, 130, 85, True, True, 0, 'Normal', 'Bolt Strike - Physical Electric move.'),
            (551, 'Blue Flare', 'Fire', 'Special', 5, 130, 85, True, False, 0, 'Normal', 'Blue Flare - Special Fire move.'),
            (552, 'Fiery Dance', 'Fire', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Fiery Dance - Special Fire move.'),
            (553, 'Freeze Shock', 'Ice', 'Physical', 5, 140, 90, True, True, 0, 'Normal', 'Freeze Shock - Physical Ice move.'),
            (554, 'Ice Burn', 'Ice', 'Special', 5, 140, 90, True, False, 0, 'Normal', 'Ice Burn - Special Ice move.'),
            (555, 'Snarl', 'Dark', 'Special', 15, 55, 95, True, False, 0, 'All_Adjacent_Foes', 'Snarl - Special Dark move.'),
            (556, 'Icicle Crash', 'Ice', 'Physical', 10, 85, 90, True, True, 0, 'Normal', 'Icicle Crash - Physical Ice move.'),
            (557, 'V-create', 'Fire', 'Physical', 5, 180, 95, True, True, 0, 'Normal', 'V-create - Physical Fire move.'),
            (558, 'Fusion Flare', 'Fire', 'Special', 5, 100, 100, True, False, 0, 'Normal', 'Fusion Flare - Special Fire move.'),
            (559, 'Fusion Bolt', 'Electric', 'Physical', 5, 100, 100, True, True, 0, 'Normal', 'Fusion Bolt - Physical Electric move.'),
            (560, 'Flying Press', 'Fighting', 'Physical', 10, 100, 95, True, True, 0, 'Normal', 'Flying Press - Physical Fighting move.'),
            (561, 'Mat Block', 'Fighting', 'Status', 10, None, None, False, False, 0, 'Normal', 'Mat Block - Status Fighting move.'),
            (562, 'Belch', 'Poison', 'Special', 10, 120, 90, True, False, 0, 'Normal', 'Belch - Special Poison move.'),
            (563, 'Rototiller', 'Ground', 'Status', 10, None, None, False, False, 0, 'Normal', 'Rototiller - Status Ground move.'),
            (564, 'Sticky Web', 'Bug', 'Status', 20, None, None, False, False, 0, 'Opponents_Field', 'Sticky Web - Status Bug move.'),
            (565, 'Fell Stinger', 'Bug', 'Physical', 25, 50, 100, True, True, 0, 'Normal', 'Fell Stinger - Physical Bug move.'),
            (566, 'Phantom Force', 'Ghost', 'Physical', 10, 90, 100, True, True, 0, 'Normal', 'Phantom Force - Physical Ghost move.'),
            (567, 'Trick-or-Treat', 'Ghost', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Trick-or-Treat - Status Ghost move.'),
            (568, 'Noble Roar', 'Normal', 'Status', 30, None, 100, False, False, 0, 'Normal', 'Noble Roar - Status Normal move.'),
            (569, 'Ion Deluge', 'Electric', 'Status', 25, None, None, False, False, 0, 'Normal', 'Ion Deluge - Status Electric move.'),
            (570, 'Parabolic Charge', 'Electric', 'Special', 20, 65, 100, True, False, 0, 'All_Adjacent', 'Parabolic Charge - Special Electric move.'),
            (571, "Forest's Curse", 'Grass', 'Status', 20, None, 100, False, False, 0, 'Normal', "Forest's Curse - Status Grass move."),
            (572, 'Petal Blizzard', 'Grass', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'Petal Blizzard - Physical Grass move.'),
            (573, 'Freeze-Dry', 'Ice', 'Special', 20, 70, 100, True, False, 0, 'Normal', 'Freeze-Dry - Special Ice move.'),
            (574, 'Disarming Voice', 'Fairy', 'Special', 15, 40, None, True, False, 0, 'Normal', 'Disarming Voice - Special Fairy move.'),
            (575, 'Parting Shot', 'Dark', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Parting Shot - Status Dark move.'),
            (576, 'Topsy-Turvy', 'Dark', 'Status', 20, None, None, False, False, 0, 'Normal', 'Topsy-Turvy - Status Dark move.'),
            (577, 'Draining Kiss', 'Fairy', 'Special', 10, 50, 100, True, False, 0, 'Normal', 'Draining Kiss - Special Fairy move.'),
            (578, 'Crafty Shield', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Normal', 'Crafty Shield - Status Fairy move.'),
            (579, 'Flower Shield', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Normal', 'Flower Shield - Status Fairy move.'),
            (580, 'Grassy Terrain', 'Grass', 'Status', 10, None, None, False, False, 0, 'Field', 'Grassy Terrain - Status Grass move.'),
            (581, 'Misty Terrain', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Field', 'Misty Terrain - Status Fairy move.'),
            (582, 'Electrify', 'Electric', 'Status', 20, None, None, False, False, 0, 'Normal', 'Electrify - Status Electric move.'),
            (583, 'Play Rough', 'Fairy', 'Physical', 10, 90, 90, True, True, 0, 'Normal', 'Play Rough - Physical Fairy move.'),
            (584, 'Fairy Wind', 'Fairy', 'Special', 30, 40, 100, True, False, 0, 'Normal', 'Fairy Wind - Special Fairy move.'),
            (585, 'Moonblast', 'Fairy', 'Special', 15, 95, 100, True, False, 0, 'Normal', 'Moonblast - Special Fairy move.'),
            (586, 'Boomburst', 'Normal', 'Special', 10, 140, 100, True, False, 0, 'All_Adjacent', 'Boomburst - Special Normal move.'),
            (587, 'Fairy Lock', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Normal', 'Fairy Lock - Status Fairy move.'),
            (588, "King's Shield", 'Steel', 'Status', 10, None, None, False, False, 4, 'Normal', "King's Shield - Status Steel move."),
            (589, 'Play Nice', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Play Nice - Status Normal move.'),
            (590, 'Confide', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Confide - Status Normal move.'),
            (591, 'Diamond Storm', 'Rock', 'Physical', 5, 100, 95, True, True, 0, 'Normal', 'Diamond Storm - Physical Rock move.'),
            (592, 'Steam Eruption', 'Water', 'Special', 5, 110, 95, True, False, 0, 'Normal', 'Steam Eruption - Special Water move.'),
            (593, 'Hyperspace Hole', 'Psychic', 'Special', 5, 80, None, True, False, 0, 'Normal', 'Hyperspace Hole - Special Psychic move.'),
            (594, 'Water Shuriken', 'Water', 'Special', 20, 15, 100, True, False, 0, 'Normal', 'Water Shuriken - Special Water move.'),
            (595, 'Mystical Fire', 'Fire', 'Special', 10, 75, 100, True, False, 0, 'Normal', 'Mystical Fire - Special Fire move.'),
            (596, 'Spiky Shield', 'Grass', 'Status', 10, None, None, False, False, 4, 'Normal', 'Spiky Shield - Status Grass move.'),
            (597, 'Aromatic Mist', 'Fairy', 'Status', 20, None, None, False, False, 0, 'Normal', 'Aromatic Mist - Status Fairy move.'),
            (598, 'Eerie Impulse', 'Electric', 'Status', 15, None, 100, False, False, 0, 'Normal', 'Eerie Impulse - Status Electric move.'),
            (599, 'Venom Drench', 'Poison', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Venom Drench - Status Poison move.'),
            (600, 'Powder', 'Bug', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Powder - Status Bug move.'),
            (601, 'Geomancy', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Normal', 'Geomancy - Status Fairy move.'),
            (602, 'Magnetic Flux', 'Electric', 'Status', 20, None, None, False, False, 0, 'Normal', 'Magnetic Flux - Status Electric move.'),
            (603, 'Happy Hour', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Happy Hour - Status Normal move.'),
            (604, 'Electric Terrain', 'Electric', 'Status', 10, None, None, False, False, 0, 'Field', 'Electric Terrain - Status Electric move.'),
            (605, 'Dazzling Gleam', 'Fairy', 'Special', 10, 80, 100, True, False, 0, 'All_Adjacent_Foes', 'Dazzling Gleam - Special Fairy move.'),
            (606, 'Celebrate', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Celebrate - Status Normal move.'),
            (607, 'Hold Hands', 'Normal', 'Status', 40, None, None, False, False, 0, 'Normal', 'Hold Hands - Status Normal move.'),
            (608, 'Baby-Doll Eyes', 'Fairy', 'Status', 30, None, 100, False, False, 0, 'Normal', 'Baby-Doll Eyes - Status Fairy move.'),
            (609, 'Nuzzle', 'Electric', 'Physical', 20, 20, 100, True, True, 0, 'Normal', 'Nuzzle - Physical Electric move.'),
            (610, 'Hold Back', 'Normal', 'Physical', 40, 40, 100, True, True, 0, 'Normal', 'Hold Back - Physical Normal move.'),
            (611, 'Infestation', 'Bug', 'Special', 20, 20, 100, True, False, 0, 'Normal', 'Infestation - Special Bug move.'),
            (612, 'Power-Up Punch', 'Fighting', 'Physical', 20, 40, 100, True, True, 0, 'Normal', 'Power-Up Punch - Physical Fighting move.'),
            (613, 'Oblivion Wing', 'Flying', 'Special', 10, 80, 100, True, False, 0, 'Normal', 'Oblivion Wing - Special Flying move.'),
            (614, 'Thousand Arrows', 'Ground', 'Physical', 10, 90, 100, True, True, 0, 'Normal', 'Thousand Arrows - Physical Ground move.'),
            (615, 'Thousand Waves', 'Ground', 'Physical', 10, 90, 100, True, True, 0, 'Normal', 'Thousand Waves - Physical Ground move.'),
            (616, "Land's Wrath", 'Ground', 'Physical', 10, 90, 100, True, True, 0, 'Normal', "Land's Wrath - Physical Ground move."),
            (617, 'Light of Ruin', 'Fairy', 'Special', 5, 140, 90, True, False, 0, 'Normal', 'Light of Ruin - Special Fairy move.'),
            (618, 'Origin Pulse', 'Water', 'Special', 10, 110, 85, True, False, 0, 'Normal', 'Origin Pulse - Special Water move.'),
            (619, 'Precipice Blades', 'Ground', 'Physical', 10, 120, 85, True, True, 0, 'Normal', 'Precipice Blades - Physical Ground move.'),
            (620, 'Dragon Ascent', 'Flying', 'Physical', 5, 120, 100, True, True, 0, 'Normal', 'Dragon Ascent - Physical Flying move.'),
            (621, 'Hyperspace Fury', 'Dark', 'Physical', 5, 100, None, True, True, 0, 'Normal', 'Hyperspace Fury - Physical Dark move.'),
            (622, 'Breakneck Blitz', 'Normal', 'Status', 1, None, None, False, False, 0, 'Normal', 'Breakneck Blitz - Status Normal move.'),
            (624, 'All-Out Pummeling', 'Fighting', 'Status', 1, None, None, False, False, 0, 'Normal', 'All-Out Pummeling - Status Fighting move.'),
            (626, 'Supersonic Skystrike', 'Flying', 'Status', 1, None, None, False, False, 0, 'Normal', 'Supersonic Skystrike - Status Flying move.'),
            (628, 'Acid Downpour', 'Poison', 'Status', 1, None, None, False, False, 0, 'Normal', 'Acid Downpour - Status Poison move.'),
            (630, 'Tectonic Rage', 'Ground', 'Status', 1, None, None, False, False, 0, 'Normal', 'Tectonic Rage - Status Ground move.'),
            (632, 'Continental Crush', 'Rock', 'Status', 1, None, None, False, False, 0, 'Normal', 'Continental Crush - Status Rock move.'),
            (634, 'Savage Spin-Out', 'Bug', 'Status', 1, None, None, False, False, 0, 'Normal', 'Savage Spin-Out - Status Bug move.'),
            (636, 'Never-Ending Nightmare', 'Ghost', 'Status', 1, None, None, False, False, 0, 'Normal', 'Never-Ending Nightmare - Status Ghost move.'),
            (638, 'Corkscrew Crash', 'Steel', 'Status', 1, None, None, False, False, 0, 'Normal', 'Corkscrew Crash - Status Steel move.'),
            (640, 'Inferno Overdrive', 'Fire', 'Status', 1, None, None, False, False, 0, 'Normal', 'Inferno Overdrive - Status Fire move.'),
            (642, 'Hydro Vortex', 'Water', 'Status', 1, None, None, False, False, 0, 'Normal', 'Hydro Vortex - Status Water move.'),
            (644, 'Bloom Doom', 'Grass', 'Status', 1, None, None, False, False, 0, 'Normal', 'Bloom Doom - Status Grass move.'),
            (646, 'Gigavolt Havoc', 'Electric', 'Status', 1, None, None, False, False, 0, 'Normal', 'Gigavolt Havoc - Status Electric move.'),
            (648, 'Shattered Psyche', 'Psychic', 'Status', 1, None, None, False, False, 0, 'Normal', 'Shattered Psyche - Status Psychic move.'),
            (650, 'Subzero Slammer', 'Ice', 'Status', 1, None, None, False, False, 0, 'Normal', 'Subzero Slammer - Status Ice move.'),
            (652, 'Devastating Drake', 'Dragon', 'Status', 1, None, None, False, False, 0, 'Normal', 'Devastating Drake - Status Dragon move.'),
            (654, 'Black Hole Eclipse', 'Dark', 'Status', 1, None, None, False, False, 0, 'Normal', 'Black Hole Eclipse - Status Dark move.'),
            (656, 'Twinkle Tackle', 'Fairy', 'Status', 1, None, None, False, False, 0, 'Normal', 'Twinkle Tackle - Status Fairy move.'),
            (658, 'Catastropika', 'Electric', 'Physical', 1, 210, None, True, True, 0, 'Normal', 'Catastropika - Physical Electric move.'),
            (659, 'Shore Up', 'Ground', 'Status', 5, None, None, False, False, 0, 'Normal', 'Shore Up - Status Ground move.'),
            (660, 'First Impression', 'Bug', 'Physical', 10, 90, 100, True, True, 1, 'Normal', 'First Impression - Physical Bug move.'),
            (661, 'Baneful Bunker', 'Poison', 'Status', 10, None, None, False, False, 4, 'Normal', 'Baneful Bunker - Status Poison move.'),
            (662, 'Spirit Shackle', 'Ghost', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Spirit Shackle - Physical Ghost move.'),
            (663, 'Darkest Lariat', 'Dark', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'Darkest Lariat - Physical Dark move.'),
            (664, 'Sparkling Aria', 'Water', 'Special', 10, 90, 100, True, False, 0, 'Normal', 'Sparkling Aria - Special Water move.'),
            (665, 'Ice Hammer', 'Ice', 'Physical', 10, 100, 90, True, True, 0, 'Normal', 'Ice Hammer - Physical Ice move.'),
            (666, 'Floral Healing', 'Fairy', 'Status', 10, None, None, False, False, 0, 'Normal', 'Floral Healing - Status Fairy move.'),
            (667, 'High Horsepower', 'Ground', 'Physical', 10, 95, 95, True, True, 0, 'Normal', 'High Horsepower - Physical Ground move.'),
            (668, 'Strength Sap', 'Grass', 'Status', 10, None, 100, False, False, 0, 'Normal', 'Strength Sap - Status Grass move.'),
            (669, 'Solar Blade', 'Grass', 'Physical', 10, 125, 100, True, True, 0, 'Normal', 'Solar Blade - Physical Grass move.'),
            (670, 'Leafage', 'Grass', 'Physical', 40, 40, 100, True, True, 0, 'Normal', 'Leafage - Physical Grass move.'),
            (671, 'Spotlight', 'Normal', 'Status', 15, None, None, False, False, 0, 'Normal', 'Spotlight - Status Normal move.'),
            (672, 'Toxic Thread', 'Poison', 'Status', 20, None, 100, False, False, 0, 'Normal', 'Toxic Thread - Status Poison move.'),
            (673, 'Laser Focus', 'Normal', 'Status', 30, None, None, False, False, 0, 'Normal', 'Laser Focus - Status Normal move.'),
            (674, 'Gear Up', 'Steel', 'Status', 20, None, None, False, False, 0, 'Normal', 'Gear Up - Status Steel move.'),
            (675, 'Throat Chop', 'Dark', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Throat Chop - Physical Dark move.'),
            (676, 'Pollen Puff', 'Bug', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'Pollen Puff - Special Bug move.'),
            (677, 'Anchor Shot', 'Steel', 'Physical', 20, 80, 100, True, True, 0, 'Normal', 'Anchor Shot - Physical Steel move.'),
            (678, 'Psychic Terrain', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Field', 'Psychic Terrain - Status Psychic move.'),
            (679, 'Lunge', 'Bug', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Lunge - Physical Bug move.'),
            (680, 'Fire Lash', 'Fire', 'Physical', 15, 80, 100, True, True, 0, 'Normal', 'Fire Lash - Physical Fire move.'),
            (681, 'Power Trip', 'Dark', 'Physical', 10, 20, 100, True, True, 0, 'Normal', 'Power Trip - Physical Dark move.'),
            (682, 'Burn Up', 'Fire', 'Special', 5, 130, 100, True, False, 0, 'Normal', 'Burn Up - Special Fire move.'),
            (683, 'Speed Swap', 'Psychic', 'Status', 10, None, None, False, False, 0, 'Normal', 'Speed Swap - Status Psychic move.'),
            (684, 'Smart Strike', 'Steel', 'Physical', 10, 70, None, True, True, 0, 'Normal', 'Smart Strike - Physical Steel move.'),
            (685, 'Purify', 'Poison', 'Status', 20, None, None, False, False, 0, 'Normal', 'Purify - Status Poison move.'),
            (686, 'Revelation Dance', 'Normal', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'Revelation Dance - Special Normal move.'),
            (687, 'Core Enforcer', 'Dragon', 'Special', 10, 100, 100, True, False, 0, 'Normal', 'Core Enforcer - Special Dragon move.'),
            (688, 'Trop Kick', 'Grass', 'Physical', 15, 70, 100, True, True, 0, 'Normal', 'Trop Kick - Physical Grass move.'),
            (689, 'Instruct', 'Psychic', 'Status', 15, None, None, False, False, 0, 'Normal', 'Instruct - Status Psychic move.'),
            (690, 'Beak Blast', 'Flying', 'Physical', 15, 100, 100, True, True, 0, 'Normal', 'Beak Blast - Physical Flying move.'),
            (691, 'Clanging Scales', 'Dragon', 'Special', 5, 110, 100, True, False, 0, 'Normal', 'Clanging Scales - Special Dragon move.'),
            (692, 'Dragon Hammer', 'Dragon', 'Physical', 15, 90, 100, True, True, 0, 'Normal', 'Dragon Hammer - Physical Dragon move.'),
            (693, 'Brutal Swing', 'Dark', 'Physical', 20, 60, 100, True, True, 0, 'Normal', 'Brutal Swing - Physical Dark move.'),
            (694, 'Aurora Veil', 'Ice', 'Status', 20, None, None, False, False, 0, 'UserSide', 'Aurora Veil - Status Ice move.'),
            (695, 'Sinister Arrow Raid', 'Ghost', 'Physical', 1, 180, None, True, True, 0, 'Normal', 'Sinister Arrow Raid - Physical Ghost move.'),
            (696, 'Malicious Moonsault', 'Dark', 'Physical', 1, 180, None, True, True, 0, 'Normal', 'Malicious Moonsault - Physical Dark move.'),
            (697, 'Oceanic Operetta', 'Water', 'Special', 1, 195, None, True, False, 0, 'Normal', 'Oceanic Operetta - Special Water move.'),
            (698, 'Guardian of Alola', 'Fairy', 'Special', 1, None, None, False, False, 0, 'Normal', 'Guardian of Alola - Special Fairy move.'),
            (699, 'Soul-Stealing 7-Star Strike', 'Ghost', 'Physical', 1, 195, None, True, True, 0, 'Normal', 'Soul-Stealing 7-Star Strike - Physical Ghost move.'),
            (700, 'Stoked Sparksurfer', 'Electric', 'Special', 1, 175, None, True, False, 0, 'Normal', 'Stoked Sparksurfer - Special Electric move.'),
            (701, 'Pulverizing Pancake', 'Normal', 'Physical', 1, 210, None, True, True, 0, 'Normal', 'Pulverizing Pancake - Physical Normal move.'),
            (702, 'Extreme Evoboost', 'Normal', 'Status', 1, None, None, False, False, 0, 'Normal', 'Extreme Evoboost - Status Normal move.'),
            (703, 'Genesis Supernova', 'Psychic', 'Special', 1, 185, None, True, False, 0, 'Normal', 'Genesis Supernova - Special Psychic move.'),
            (704, 'Shell Trap', 'Fire', 'Special', 5, 150, 100, True, False, 0, 'Normal', 'Shell Trap - Special Fire move.'),
            (705, 'Fleur Cannon', 'Fairy', 'Special', 5, 130, 90, True, False, 0, 'Normal', 'Fleur Cannon - Special Fairy move.'),
            (706, 'Psychic Fangs', 'Psychic', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'Psychic Fangs - Physical Psychic move.'),
            (707, 'Stomping Tantrum', 'Ground', 'Physical', 10, 75, 100, True, True, 0, 'Normal', 'Stomping Tantrum - Physical Ground move.'),
            (708, 'Shadow Bone', 'Ghost', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'Shadow Bone - Physical Ghost move.'),
            (709, 'Accelerock', 'Rock', 'Physical', 20, 40, 100, True, True, 1, 'Normal', 'Accelerock - Physical Rock move.'),
            (710, 'Liquidation', 'Water', 'Physical', 10, 85, 100, True, True, 0, 'Normal', 'Liquidation - Physical Water move.'),
            (711, 'Prismatic Laser', 'Psychic', 'Special', 10, 160, 100, True, False, 0, 'Normal', 'Prismatic Laser - Special Psychic move.'),
            (712, 'Spectral Thief', 'Ghost', 'Physical', 10, 90, 100, True, True, 0, 'Normal', 'Spectral Thief - Physical Ghost move.'),
            (713, 'Sunsteel Strike', 'Steel', 'Physical', 5, 100, 100, True, True, 0, 'Normal', 'Sunsteel Strike - Physical Steel move.'),
            (714, 'Moongeist Beam', 'Ghost', 'Special', 5, 100, 100, True, False, 0, 'Normal', 'Moongeist Beam - Special Ghost move.'),
            (715, 'Tearful Look', 'Normal', 'Status', 20, None, None, False, False, 0, 'Normal', 'Tearful Look - Status Normal move.'),
            (716, 'Zing Zap', 'Electric', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Zing Zap - Physical Electric move.'),
            (717, "Nature's Madness", 'Fairy', 'Special', 10, None, 90, False, False, 0, 'Normal', "Nature's Madness - Special Fairy move."),
            (718, 'Multi-Attack', 'Normal', 'Physical', 10, 120, 100, True, True, 0, 'Normal', 'Multi-Attack - Physical Normal move.'),
            (719, '10,000,000 Volt Thunderbolt', 'Electric', 'Special', 1, 195, None, True, False, 0, 'Normal', '10,000,000 Volt Thunderbolt - Special Electric move.'),
            (720, 'Mind Blown', 'Fire', 'Special', 5, 150, 100, True, False, 0, 'Normal', 'Mind Blown - Special Fire move.'),
            (721, 'Plasma Fists', 'Electric', 'Physical', 15, 100, 100, True, True, 0, 'Normal', 'Plasma Fists - Physical Electric move.'),
            (722, 'Photon Geyser', 'Psychic', 'Special', 5, 100, 100, True, False, 0, 'Normal', 'Photon Geyser - Special Psychic move.'),
            (723, 'Light That Burns the Sky', 'Psychic', 'Special', 1, 200, None, True, False, 0, 'Normal', 'Light That Burns the Sky - Special Psychic move.'),
            (724, 'Searing Sunraze Smash', 'Steel', 'Physical', 1, 200, None, True, True, 0, 'Normal', 'Searing Sunraze Smash - Physical Steel move.'),
            (725, 'Menacing Moonraze Maelstrom', 'Ghost', 'Special', 1, 200, None, True, False, 0, 'Normal', 'Menacing Moonraze Maelstrom - Special Ghost move.'),
            (726, "Let's Snuggle Forever", 'Fairy', 'Physical', 1, 190, None, True, True, 0, 'Normal', "Let's Snuggle Forever - Physical Fairy move."),
            (727, 'Splintered Stormshards', 'Rock', 'Physical', 1, 190, None, True, True, 0, 'Normal', 'Splintered Stormshards - Physical Rock move.'),
            (728, 'Clangorous Soulblaze', 'Dragon', 'Special', 1, 185, None, True, False, 0, 'Normal', 'Clangorous Soulblaze - Special Dragon move.'),
            (729, 'Zippy Zap', 'Electric', 'Physical', 10, 80, 100, True, True, 0, 'Normal', 'Zippy Zap - Physical Electric move.'),
            (730, 'Splishy Splash', 'Water', 'Special', 15, 90, 100, True, False, 0, 'Normal', 'Splishy Splash - Special Water move.'),
            (731, 'Floaty Fall', 'Flying', 'Physical', 15, 90, 95, True, True, 0, 'Normal', 'Floaty Fall - Physical Flying move.'),
            (732, 'Pika Papow', 'Electric', 'Special', 20, None, None, False, False, 0, 'Normal', 'Pika Papow - Special Electric move.'),
            (733, 'Bouncy Bubble', 'Water', 'Special', 20, 60, 100, True, False, 0, 'Normal', 'Bouncy Bubble - Special Water move.'),
            (734, 'Buzzy Buzz', 'Electric', 'Special', 20, 60, 100, True, False, 0, 'Normal', 'Buzzy Buzz - Special Electric move.'),
            (735, 'Sizzly Slide', 'Fire', 'Physical', 20, 60, 100, True, True, 0, 'Normal', 'Sizzly Slide - Physical Fire move.'),
            (736, 'Glitzy Glow', 'Psychic', 'Special', 15, 80, 95, True, False, 0, 'Normal', 'Glitzy Glow - Special Psychic move.'),
            (737, 'Baddy Bad', 'Dark', 'Special', 15, 80, 95, True, False, 0, 'Normal', 'Baddy Bad - Special Dark move.'),
            (738, 'Sappy Seed', 'Grass', 'Physical', 10, 100, 90, True, True, 0, 'Normal', 'Sappy Seed - Physical Grass move.'),
            (739, 'Freezy Frost', 'Ice', 'Special', 10, 100, 90, True, False, 0, 'Normal', 'Freezy Frost - Special Ice move.'),
            (740, 'Sparkly Swirl', 'Fairy', 'Special', 5, 120, 85, True, False, 0, 'Normal', 'Sparkly Swirl - Special Fairy move.'),
            (741, 'Veevee Volley', 'Normal', 'Physical', 20, None, None, False, True, 0, 'Normal', 'Veevee Volley - Physical Normal move.'),
            (742, 'Double Iron Bash', 'Steel', 'Physical', 5, 60, 100, True, True, 0, 'Normal', 'Double Iron Bash - Physical Steel move.'),
        ]

        cursor.executemany('''
            INSERT OR REPLACE INTO moves
            (id, name, type, category, pp, power, accuracy, causes_damage, makes_contact, priority, target_type, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', moves)

        print(f'Successfully inserted {len(moves)} moves')

    def _insert_pokemon_evolutions(self, cursor):
        """Insert pokemon evolution data from exported file"""
        try:
            # Import the exported data
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from pokemon_evolutions_export import POKEMON_EVOLUTIONS
            
            cursor.executemany('''
                INSERT INTO pokemon_evolutions (pokemon_id, evolves_to_id, evolution_level)
                VALUES (?, ?, ?)
            ''', POKEMON_EVOLUTIONS)
            print(f'Inserted {len(POKEMON_EVOLUTIONS)} pokemon evolution entries')
        except ImportError:
            print('⚠️  Warning: pokemon_evolutions_export.py not found. Evolutions table will be empty.')
            print('   Run: py export_data.py to generate this file from existing database.')

    def _insert_pokemon_learnsets(self, cursor):
        """Insert pokemon learnset data from exported file"""
        try:
            # Import the exported data
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from pokemon_learnsets_export import POKEMON_LEARNSETS
            
            cursor.executemany('''
                INSERT INTO pokemon_learnsets (pokemon_id, move_id, learn_method, learn_level, form)
                VALUES (?, ?, ?, ?, ?)
            ''', POKEMON_LEARNSETS)
            print(f'Inserted {len(POKEMON_LEARNSETS)} pokemon learnset entries')
        except ImportError:
            print('⚠️  Warning: pokemon_learnsets_export.py not found. Learnsets table will be empty.')
            print('   Run: py export_data.py to generate this file from existing database.')

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

    # endregion Data insertion


def get_all_moves():
    """Get all moves"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM moves ORDER BY name')
    results = cursor.fetchall()
    conn.close()
    return results


def get_available_moves_for_level(pokemon_id, current_level, count=4):
    """
    Get the most recent moves available for a Pokemon at a given level.
    This is useful for generating a moveset for a Pokemon at a specific level.
    
    Args:
        pokemon_id: Pokemon ID
        current_level: Current level of the Pokemon
        count: Number of most recent moves to return (default 4)
    
    Returns:
        List of dicts with move id, name, and learn_level (ordered by most recent first)
    """
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.id, m.name, pl.learn_level
        FROM pokemon_learnsets pl
        JOIN moves m ON pl.move_id = m.id
        WHERE pl.pokemon_id = ? AND pl.learn_method = 'levelup' AND pl.learn_level <= ?
        ORDER BY pl.learn_level DESC
        LIMIT ?
    ''', (pokemon_id, current_level, count))
    
    moves = []
    for row in cursor.fetchall():
        moves.append({
            'id': row[0],
            'name': row[1],
            'learn_level': row[2]
        })
    
    conn.close()
    return moves


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


def get_moves_at_level(pokemon_id, level):
    """
    Get moves a Pokemon learns at a specific level
    
    Args:
        pokemon_id: Pokemon ID
        level: Specific level to check
    
    Returns:
        List of dicts with move id and name
    """
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.id, m.name
        FROM pokemon_learnsets pl
        JOIN moves m ON pl.move_id = m.id
        WHERE pl.pokemon_id = ? AND pl.learn_method = 'levelup' AND pl.learn_level = ?
        ORDER BY m.name
    ''', (pokemon_id, level))
    
    moves = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    conn.close()
    return moves


# ========== POKEMON LEARNSET FUNCTIONS ==========

def get_pokemon_learnset(pokemon_id, max_level=None):
    """
    Get all moves a Pokemon can learn by leveling up
    
    Args:
        pokemon_id: Pokemon ID
        max_level: Optional maximum level to filter moves (e.g., get moves up to level 50)
    
    Returns:
        List of dicts with move info: id, name, learn_level, type, category, power, accuracy, pp
    """
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT m.id, m.name, pl.learn_level, m.type, m.category, m.power, m.accuracy, m.pp
        FROM pokemon_learnsets pl
        JOIN moves m ON pl.move_id = m.id
        WHERE pl.pokemon_id = ? AND pl.learn_method = 'levelup'
    '''
    
    if max_level:
        query += ' AND pl.learn_level <= ?'
        cursor.execute(query + ' ORDER BY pl.learn_level', (pokemon_id, max_level))
    else:
        cursor.execute(query + ' ORDER BY pl.learn_level', (pokemon_id,))
    
    moves = []
    for row in cursor.fetchall():
        moves.append({
            'id': row[0],
            'name': row[1],
            'learn_level': row[2],
            'type': row[3],
            'category': row[4],
            'power': row[5],
            'accuracy': row[6],
            'pp': row[7]
        })
    
    conn.close()
    return moves


def search_moves_by_type(move_type):
    """Search moves by type"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM moves WHERE type = ? ORDER BY name', (move_type,))
    results = cursor.fetchall()
    conn.close()
    return results