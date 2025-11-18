import sqlite3
import os
from pathlib import Path

class PokemonDataManager:
    def __init__(self, db_path="data/pokemon_battle.db"):
        self.db_path = db_path
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def initialize_pokemon_data(self):
        """Create Pokémon table and insert all 151 Pokémon"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create Pokémon table
        self._create_pokemon_table(cursor)
        
        # Insert all 151 Pokémon
        print("Inserting Pokémon data...")
        self._insert_pokemon(cursor)
        
        conn.commit()
        conn.close()
        print("✅ Pokémon data initialized successfully!")

    def _create_pokemon_table(self, cursor):
        """Create the Pokémon table"""
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pokemon (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            type1 TEXT NOT NULL,
            type2 TEXT,
            hp INTEGER NOT NULL,
            attack INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            special_attack INTEGER NOT NULL,
            special_defense INTEGER NOT NULL,
            speed INTEGER NOT NULL,
            total_stats INTEGER NOT NULL
        )
        ''')

    def _insert_pokemon(self, cursor):
        """Insert all 151 Pokémon with their statistics"""
        pokemon_data = [
            (1, 'Bulbasaur', 'Grass', 'Poison', 45, 49, 49, 65, 65, 45, 318),
            (2, 'Ivysaur', 'Grass', 'Poison', 60, 62, 63, 80, 80, 60, 405),
            (3, 'Venusaur', 'Grass', 'Poison', 80, 82, 83, 100, 100, 80, 525),
            (4, 'Charmander', 'Fire', None, 39, 52, 43, 60, 50, 65, 309),
            (5, 'Charmeleon', 'Fire', None, 58, 64, 58, 80, 65, 80, 405),
            (6, 'Charizard', 'Fire', 'Flying', 78, 84, 78, 109, 85, 100, 534),
            (7, 'Squirtle', 'Water', None, 44, 48, 65, 50, 64, 43, 314),
            (8, 'Wartortle', 'Water', None, 59, 63, 80, 65, 80, 58, 405),
            (9, 'Blastoise', 'Water', None, 79, 83, 100, 85, 105, 78, 530),
            (10, 'Caterpie', 'Bug', None, 45, 30, 35, 20, 20, 45, 195),
            (11, 'Metapod', 'Bug', None, 50, 20, 55, 25, 25, 30, 205),
            (12, 'Butterfree', 'Bug', 'Flying', 60, 45, 50, 90, 80, 70, 395),
            (13, 'Weedle', 'Bug', 'Poison', 40, 35, 30, 20, 20, 50, 195),
            (14, 'Kakuna', 'Bug', 'Poison', 45, 25, 50, 25, 25, 35, 205),
            (15, 'Beedrill', 'Bug', 'Poison', 65, 90, 40, 45, 80, 75, 395),
            (16, 'Pidgey', 'Normal', 'Flying', 40, 45, 40, 35, 35, 56, 251),
            (17, 'Pidgeotto', 'Normal', 'Flying', 63, 60, 55, 50, 50, 71, 349),
            (18, 'Pidgeot', 'Normal', 'Flying', 83, 80, 75, 70, 70, 101, 479),
            (19, 'Rattata', 'Normal', None, 30, 56, 35, 25, 35, 72, 253),
            (20, 'Raticate', 'Normal', None, 55, 81, 60, 50, 70, 97, 413),
            (21, 'Spearow', 'Normal', 'Flying', 40, 60, 30, 31, 31, 70, 262),
            (22, 'Fearow', 'Normal', 'Flying', 65, 90, 65, 61, 61, 100, 442),
            (23, 'Ekans', 'Poison', None, 35, 60, 44, 40, 54, 55, 288),
            (24, 'Arbok', 'Poison', None, 60, 95, 69, 65, 79, 80, 448),
            (25, 'Pikachu', 'Electric', None, 35, 55, 40, 50, 50, 90, 320),
            (26, 'Raichu', 'Electric', None, 60, 90, 55, 90, 80, 110, 485),
            (27, 'Sandshrew', 'Ground', None, 50, 75, 85, 20, 30, 40, 300),
            (28, 'Sandslash', 'Ground', None, 75, 100, 110, 45, 55, 65, 450),
            (29, 'Nidoran♀', 'Poison', None, 55, 47, 52, 40, 40, 41, 275),
            (30, 'Nidorina', 'Poison', None, 70, 62, 67, 55, 55, 56, 365),
            (31, 'Nidoqueen', 'Poison', 'Ground', 90, 92, 87, 75, 85, 76, 505),
            (32, 'Nidoran♂', 'Poison', None, 46, 57, 40, 40, 40, 50, 273),
            (33, 'Nidorino', 'Poison', None, 61, 72, 57, 55, 55, 65, 365),
            (34, 'Nidoking', 'Poison', 'Ground', 81, 102, 77, 85, 75, 85, 505),
            (35, 'Clefairy', 'Fairy', None, 70, 45, 48, 60, 65, 35, 323),
            (36, 'Clefable', 'Fairy', None, 95, 70, 73, 95, 90, 60, 483),
            (37, 'Vulpix', 'Fire', None, 38, 41, 40, 50, 65, 65, 299),
            (38, 'Ninetales', 'Fire', None, 73, 76, 75, 81, 100, 100, 505),
            (39, 'Jigglypuff', 'Normal', 'Fairy', 115, 45, 20, 45, 25, 20, 270),
            (40, 'Wigglytuff', 'Normal', 'Fairy', 140, 70, 45, 85, 50, 45, 435),
            (41, 'Zubat', 'Poison', 'Flying', 40, 45, 35, 30, 40, 55, 245),
            (42, 'Golbat', 'Poison', 'Flying', 75, 80, 70, 65, 75, 90, 455),
            (43, 'Oddish', 'Grass', 'Poison', 45, 50, 55, 75, 65, 30, 320),
            (44, 'Gloom', 'Grass', 'Poison', 60, 65, 70, 85, 75, 40, 395),
            (45, 'Vileplume', 'Grass', 'Poison', 75, 80, 85, 110, 90, 50, 490),
            (46, 'Paras', 'Bug', 'Grass', 35, 70, 55, 45, 55, 25, 285),
            (47, 'Parasect', 'Bug', 'Grass', 60, 95, 80, 60, 80, 30, 405),
            (48, 'Venonat', 'Bug', 'Poison', 60, 55, 50, 40, 55, 45, 305),
            (49, 'Venomoth', 'Bug', 'Poison', 70, 65, 60, 90, 75, 90, 450),
            (50, 'Diglett', 'Ground', None, 10, 55, 25, 35, 45, 95, 265),
            (51, 'Dugtrio', 'Ground', None, 35, 100, 50, 50, 70, 120, 425),
            (52, 'Meowth', 'Normal', None, 40, 45, 35, 40, 40, 90, 290),
            (53, 'Persian', 'Normal', None, 65, 70, 60, 65, 65, 115, 440),
            (54, 'Psyduck', 'Water', None, 50, 52, 48, 65, 50, 55, 320),
            (55, 'Golduck', 'Water', None, 80, 82, 78, 95, 80, 85, 500),
            (56, 'Mankey', 'Fighting', None, 40, 80, 35, 35, 45, 70, 305),
            (57, 'Primeape', 'Fighting', None, 65, 105, 60, 60, 70, 95, 455),
            (58, 'Growlithe', 'Fire', None, 55, 70, 45, 70, 50, 60, 350),
            (59, 'Arcanine', 'Fire', None, 90, 110, 80, 100, 80, 95, 555),
            (60, 'Poliwag', 'Water', None, 40, 50, 40, 40, 40, 90, 300),
            (61, 'Poliwhirl', 'Water', None, 65, 65, 65, 50, 50, 90, 385),
            (62, 'Poliwrath', 'Water', 'Fighting', 90, 95, 95, 70, 90, 70, 510),
            (63, 'Abra', 'Psychic', None, 25, 20, 15, 105, 55, 90, 310),
            (64, 'Kadabra', 'Psychic', None, 40, 35, 30, 120, 70, 105, 400),
            (65, 'Alakazam', 'Psychic', None, 55, 50, 45, 135, 95, 120, 500),
            (66, 'Machop', 'Fighting', None, 70, 80, 50, 35, 35, 35, 305),
            (67, 'Machoke', 'Fighting', None, 80, 100, 70, 50, 60, 45, 405),
            (68, 'Machamp', 'Fighting', None, 90, 130, 80, 65, 85, 55, 505),
            (69, 'Bellsprout', 'Grass', 'Poison', 50, 75, 35, 70, 30, 40, 300),
            (70, 'Weepinbell', 'Grass', 'Poison', 65, 90, 50, 85, 45, 55, 390),
            (71, 'Victreebel', 'Grass', 'Poison', 80, 105, 65, 100, 70, 70, 490),
            (72, 'Tentacool', 'Water', 'Poison', 40, 40, 35, 50, 100, 70, 335),
            (73, 'Tentacruel', 'Water', 'Poison', 80, 70, 65, 80, 120, 100, 515),
            (74, 'Geodude', 'Rock', 'Ground', 40, 80, 100, 30, 30, 20, 300),
            (75, 'Graveler', 'Rock', 'Ground', 55, 95, 115, 45, 45, 35, 390),
            (76, 'Golem', 'Rock', 'Ground', 80, 120, 130, 55, 65, 45, 495),
            (77, 'Ponyta', 'Fire', None, 50, 85, 55, 65, 65, 90, 410),
            (78, 'Rapidash', 'Fire', None, 65, 100, 70, 80, 80, 105, 500),
            (79, 'Slowpoke', 'Water', 'Psychic', 90, 65, 65, 40, 40, 15, 315),
            (80, 'Slowbro', 'Water', 'Psychic', 95, 75, 110, 100, 80, 30, 490),
            (81, 'Magnemite', 'Electric', 'Steel', 25, 35, 70, 95, 55, 45, 325),
            (82, 'Magneton', 'Electric', 'Steel', 50, 60, 95, 120, 70, 70, 465),
            (83, 'Farfetch''d', 'Normal', 'Flying', 52, 90, 55, 58, 62, 60, 377),
            (84, 'Doduo', 'Normal', 'Flying', 35, 85, 45, 35, 35, 75, 310),
            (85, 'Dodrio', 'Normal', 'Flying', 60, 110, 70, 60, 60, 110, 470),
            (86, 'Seel', 'Water', None, 65, 45, 55, 45, 70, 45, 325),
            (87, 'Dewgong', 'Water', 'Ice', 90, 70, 80, 70, 95, 70, 475),
            (88, 'Grimer', 'Poison', None, 80, 80, 50, 40, 50, 25, 325),
            (89, 'Muk', 'Poison', None, 105, 105, 75, 65, 100, 50, 500),
            (90, 'Shellder', 'Water', None, 30, 65, 100, 45, 25, 40, 305),
            (91, 'Cloyster', 'Water', 'Ice', 50, 95, 180, 85, 45, 70, 525),
            (92, 'Gastly', 'Ghost', 'Poison', 30, 35, 30, 100, 35, 80, 310),
            (93, 'Haunter', 'Ghost', 'Poison', 45, 50, 45, 115, 55, 95, 405),
            (94, 'Gengar', 'Ghost', 'Poison', 60, 65, 60, 130, 75, 110, 500),
            (95, 'Onix', 'Rock', 'Ground', 35, 45, 160, 30, 45, 70, 385),
            (96, 'Drowzee', 'Psychic', None, 60, 48, 45, 43, 90, 42, 328),
            (97, 'Hypno', 'Psychic', None, 85, 73, 70, 73, 115, 67, 483),
            (98, 'Krabby', 'Water', None, 30, 105, 90, 25, 25, 50, 325),
            (99, 'Kingler', 'Water', None, 55, 130, 115, 50, 50, 75, 475),
            (100, 'Voltorb', 'Electric', None, 40, 30, 50, 55, 55, 100, 330),
            (101, 'Electrode', 'Electric', None, 60, 50, 70, 80, 80, 150, 490),
            (102, 'Exeggcute', 'Grass', 'Psychic', 60, 40, 80, 60, 45, 40, 325),
            (103, 'Exeggutor', 'Grass', 'Psychic', 95, 95, 85, 125, 75, 55, 530),
            (104, 'Cubone', 'Ground', None, 50, 50, 95, 40, 50, 35, 320),
            (105, 'Marowak', 'Ground', None, 60, 80, 110, 50, 80, 45, 425),
            (106, 'Hitmonlee', 'Fighting', None, 50, 120, 53, 35, 110, 87, 455),
            (107, 'Hitmonchan', 'Fighting', None, 50, 105, 79, 35, 110, 76, 455),
            (108, 'Lickitung', 'Normal', None, 90, 55, 75, 60, 75, 30, 385),
            (109, 'Koffing', 'Poison', None, 40, 65, 95, 60, 45, 35, 340),
            (110, 'Weezing', 'Poison', None, 65, 90, 120, 85, 70, 60, 490),
            (111, 'Rhyhorn', 'Ground', 'Rock', 80, 85, 95, 30, 30, 25, 345),
            (112, 'Rhydon', 'Ground', 'Rock', 105, 130, 120, 45, 45, 40, 485),
            (113, 'Chansey', 'Normal', None, 250, 5, 5, 35, 105, 50, 450),
            (114, 'Tangela', 'Grass', None, 65, 55, 115, 100, 40, 60, 435),
            (115, 'Kangaskhan', 'Normal', None, 105, 95, 80, 40, 80, 90, 490),
            (116, 'Horsea', 'Water', None, 30, 40, 70, 70, 25, 60, 295),
            (117, 'Seadra', 'Water', None, 55, 65, 95, 95, 45, 85, 440),
            (118, 'Goldeen', 'Water', None, 45, 67, 60, 35, 50, 63, 320),
            (119, 'Seaking', 'Water', None, 80, 92, 65, 65, 80, 68, 450),
            (120, 'Staryu', 'Water', None, 30, 45, 55, 70, 55, 85, 340),
            (121, 'Starmie', 'Water', 'Psychic', 60, 75, 85, 100, 85, 115, 520),
            (122, 'Mr. Mime', 'Psychic', 'Fairy', 40, 45, 65, 100, 120, 90, 460),
            (123, 'Scyther', 'Bug', 'Flying', 70, 110, 80, 55, 80, 105, 500),
            (124, 'Jynx', 'Ice', 'Psychic', 65, 50, 35, 115, 95, 95, 455),
            (125, 'Electabuzz', 'Electric', None, 65, 83, 57, 95, 85, 105, 490),
            (126, 'Magmar', 'Fire', None, 65, 95, 57, 100, 85, 93, 495),
            (127, 'Pinsir', 'Bug', None, 65, 125, 100, 55, 70, 85, 500),
            (128, 'Tauros', 'Normal', None, 75, 100, 95, 40, 70, 110, 490),
            (129, 'Magikarp', 'Water', None, 20, 10, 55, 15, 20, 80, 200),
            (130, 'Gyarados', 'Water', 'Flying', 95, 125, 79, 60, 100, 81, 540),
            (131, 'Lapras', 'Water', 'Ice', 130, 85, 80, 85, 95, 60, 535),
            (132, 'Ditto', 'Normal', None, 48, 48, 48, 48, 48, 48, 288),
            (133, 'Eevee', 'Normal', None, 55, 55, 50, 45, 65, 55, 325),
            (134, 'Vaporeon', 'Water', None, 130, 65, 60, 110, 95, 65, 525),
            (135, 'Jolteon', 'Electric', None, 65, 65, 60, 110, 95, 130, 525),
            (136, 'Flareon', 'Fire', None, 65, 130, 60, 95, 110, 65, 525),
            (137, 'Porygon', 'Normal', None, 65, 60, 70, 85, 75, 40, 395),
            (138, 'Omanyte', 'Rock', 'Water', 35, 40, 100, 90, 55, 35, 355),
            (139, 'Omastar', 'Rock', 'Water', 70, 60, 125, 115, 70, 55, 495),
            (140, 'Kabuto', 'Rock', 'Water', 30, 80, 90, 55, 45, 55, 355),
            (141, 'Kabutops', 'Rock', 'Water', 60, 115, 105, 65, 70, 80, 495),
            (142, 'Aerodactyl', 'Rock', 'Flying', 80, 105, 65, 60, 75, 130, 515),
            (143, 'Snorlax', 'Normal', None, 160, 110, 65, 65, 110, 30, 540),
            (144, 'Articuno', 'Ice', 'Flying', 90, 85, 100, 95, 125, 85, 580),
            (145, 'Zapdos', 'Electric', 'Flying', 90, 90, 85, 125, 90, 100, 580),
            (146, 'Moltres', 'Fire', 'Flying', 90, 100, 90, 125, 85, 90, 580),
            (147, 'Dratini', 'Dragon', None, 41, 64, 45, 50, 50, 50, 300),
            (148, 'Dragonair', 'Dragon', None, 61, 84, 65, 70, 70, 70, 420),
            (149, 'Dragonite', 'Dragon', 'Flying', 91, 134, 95, 100, 100, 80, 600),
            (150, 'Mewtwo', 'Psychic', None, 106, 110, 90, 154, 90, 130, 680),
            (151, 'Mew', 'Psychic', None, 100, 100, 100, 100, 100, 100, 600)
        ]
        
        # Clear the table first to avoid duplicates
        cursor.execute("DELETE FROM pokemon")
        
        # Insert all Pokémon
        cursor.executemany('''
        INSERT INTO pokemon 
        (id, name, type1, type2, hp, attack, defense, special_attack, special_defense, speed, total_stats)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pokemon_data)
        
        print(f"✅ Successfully inserted {len(pokemon_data)} Pokémon")

# Helper functions to interact with Pokémon data
def get_all_pokemon():
    """Get all Pokémon"""
    db = PokemonDataManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pokemon ORDER BY id')
    results = cursor.fetchall()
    conn.close()
    return results

def get_pokemon_by_id(pokemon_id):
    """Get Pokémon by ID"""
    db = PokemonDataManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pokemon WHERE id = ?', (pokemon_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def search_pokemon_by_type(pokemon_type):
    """Search Pokémon by type"""
    db = PokemonDataManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pokemon WHERE type1 = ? OR type2 = ? ORDER BY name', (pokemon_type, pokemon_type))
    results = cursor.fetchall()
    conn.close()
    return results

def get_pokemon_by_name(name):
    """Get Pokémon by name"""
    db = PokemonDataManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pokemon WHERE name = ?', (name,))
    result = cursor.fetchone()
    conn.close()
    return result

# Main function to initialize Pokémon data
def main():
    """Initialize Pokémon database"""
    print("=== Pokémon Data Initialization ===")
    db = PokemonDataManager()
    db.initialize_pokemon_data()
    
    # Verify data was inserted
    pokemon_count = len(get_all_pokemon())
    print(f"Total Pokémon in database: {pokemon_count}")

if __name__ == "__main__":
    main()