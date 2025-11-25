import sqlite3
import os
from pathlib import Path

try:
    from .database import DatabaseManager
except ImportError:
    from database import DatabaseManager

class PokemonDataManager:
    def __init__(self, db_path="data/pokemon_battle.db"):
        self.db_manager = DatabaseManager(db_path)
        self.db_path = db_path
        
    def get_connection(self):
        """Get database connection"""
        return self.db_manager.get_connection()
    
    def initialize_pokemon_data(self):
        """Insert all 151 Pokémon (table already created by DatabaseManager)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Insert all 151 Pokémon
        print("Inserting Pokémon data...")
        self._insert_pokemon(cursor)
        
        conn.commit()
        conn.close()
        print("Pokemon data initialized successfully!")

    def _insert_pokemon(self, cursor):
        """Insert all 151 Pokémon with their statistics, evolution levels and exp curves"""
        pokemon_data = [
            # (id, name, type1, type2, hp, atk, def, sp_atk, sp_def, speed, total, evo_level, exp_curve)
            (1, 'Bulbasaur', 'Grass', 'Poison', 45, 49, 49, 65, 65, 45, 318, 16, 'medium-slow'),
            (2, 'Ivysaur', 'Grass', 'Poison', 60, 62, 63, 80, 80, 60, 405, 32, 'medium-slow'),
            (3, 'Venusaur', 'Grass', 'Poison', 80, 82, 83, 100, 100, 80, 525, None, 'medium-slow'),
            (4, 'Charmander', 'Fire', None, 39, 52, 43, 60, 50, 65, 309, 16, 'medium-slow'),
            (5, 'Charmeleon', 'Fire', None, 58, 64, 58, 80, 65, 80, 405, 36, 'medium-slow'),
            (6, 'Charizard', 'Fire', 'Flying', 78, 84, 78, 109, 85, 100, 534, None, 'medium-slow'),
            (7, 'Squirtle', 'Water', None, 44, 48, 65, 50, 64, 43, 314, 16, 'medium-slow'),
            (8, 'Wartortle', 'Water', None, 59, 63, 80, 65, 80, 58, 405, 36, 'medium-slow'),
            (9, 'Blastoise', 'Water', None, 79, 83, 100, 85, 105, 78, 530, None, 'medium-slow'),
            (10, 'Caterpie', 'Bug', None, 45, 30, 35, 20, 20, 45, 195, 7, 'medium-fast'),
            (11, 'Metapod', 'Bug', None, 50, 20, 55, 25, 25, 30, 205, 10, 'medium-fast'),
            (12, 'Butterfree', 'Bug', 'Flying', 60, 45, 50, 90, 80, 70, 395, None, 'medium-fast'),
            (13, 'Weedle', 'Bug', 'Poison', 40, 35, 30, 20, 20, 50, 195, 7, 'medium-fast'),
            (14, 'Kakuna', 'Bug', 'Poison', 45, 25, 50, 25, 25, 35, 205, 10, 'medium-fast'),
            (15, 'Beedrill', 'Bug', 'Poison', 65, 90, 40, 45, 80, 75, 395, None, 'medium-fast'),
            (16, 'Pidgey', 'Normal', 'Flying', 40, 45, 40, 35, 35, 56, 251, 18, 'medium-fast'),
            (17, 'Pidgeotto', 'Normal', 'Flying', 63, 60, 55, 50, 50, 71, 349, 36, 'medium-fast'),
            (18, 'Pidgeot', 'Normal', 'Flying', 83, 80, 75, 70, 70, 101, 479, None, 'medium-fast'),
            (19, 'Rattata', 'Normal', None, 30, 56, 35, 25, 35, 72, 253, 20, 'medium-fast'),
            (20, 'Raticate', 'Normal', None, 55, 81, 60, 50, 70, 97, 413, None, 'medium-fast'),
            (21, 'Spearow', 'Normal', 'Flying', 40, 60, 30, 31, 31, 70, 262, 20, 'medium-fast'),
            (22, 'Fearow', 'Normal', 'Flying', 65, 90, 65, 61, 61, 100, 442, None, 'medium-fast'),
            (23, 'Ekans', 'Poison', None, 35, 60, 44, 40, 54, 55, 288, 22, 'medium-fast'),
            (24, 'Arbok', 'Poison', None, 60, 95, 69, 65, 79, 80, 448, None, 'medium-fast'),
            (25, 'Pikachu', 'Electric', None, 35, 55, 40, 50, 50, 90, 320, None, 'medium-fast'),
            (26, 'Raichu', 'Electric', None, 60, 90, 55, 90, 80, 110, 485, None, 'medium-fast'),
            (27, 'Sandshrew', 'Ground', None, 50, 75, 85, 20, 30, 40, 300, 22, 'medium-fast'),
            (28, 'Sandslash', 'Ground', None, 75, 100, 110, 45, 55, 65, 450, None, 'medium-fast'),
            (29, 'Nidoran♀', 'Poison', None, 55, 47, 52, 40, 40, 41, 275, 16, 'medium-slow'),
            (30, 'Nidorina', 'Poison', None, 70, 62, 67, 55, 55, 56, 365, None, 'medium-slow'),
            (31, 'Nidoqueen', 'Poison', 'Ground', 90, 92, 87, 75, 85, 76, 505, None, 'medium-slow'),
            (32, 'Nidoran♂', 'Poison', None, 46, 57, 40, 40, 40, 50, 273, 16, 'medium-slow'),
            (33, 'Nidorino', 'Poison', None, 61, 72, 57, 55, 55, 65, 365, None, 'medium-slow'),
            (34, 'Nidoking', 'Poison', 'Ground', 81, 102, 77, 85, 75, 85, 505, None, 'medium-slow'),
            (35, 'Clefairy', 'Fairy', None, 70, 45, 48, 60, 65, 35, 323, None, 'fast'),
            (36, 'Clefable', 'Fairy', None, 95, 70, 73, 95, 90, 60, 483, None, 'fast'),
            (37, 'Vulpix', 'Fire', None, 38, 41, 40, 50, 65, 65, 299, None, 'medium-fast'),
            (38, 'Ninetales', 'Fire', None, 73, 76, 75, 81, 100, 100, 505, None, 'medium-fast'),
            (39, 'Jigglypuff', 'Normal', 'Fairy', 115, 45, 20, 45, 25, 20, 270, None, 'fast'),
            (40, 'Wigglytuff', 'Normal', 'Fairy', 140, 70, 45, 85, 50, 45, 435, None, 'fast'),
            (41, 'Zubat', 'Poison', 'Flying', 40, 45, 35, 30, 40, 55, 245, 22, 'medium-fast'),
            (42, 'Golbat', 'Poison', 'Flying', 75, 80, 70, 65, 75, 90, 455, None, 'medium-fast'),
            (43, 'Oddish', 'Grass', 'Poison', 45, 50, 55, 75, 65, 30, 320, 21, 'medium-slow'),
            (44, 'Gloom', 'Grass', 'Poison', 60, 65, 70, 85, 75, 40, 395, None, 'medium-slow'),
            (45, 'Vileplume', 'Grass', 'Poison', 75, 80, 85, 110, 90, 50, 490, None, 'medium-slow'),
            (46, 'Paras', 'Bug', 'Grass', 35, 70, 55, 45, 55, 25, 285, 24, 'medium-fast'),
            (47, 'Parasect', 'Bug', 'Grass', 60, 95, 80, 60, 80, 30, 405, None, 'medium-fast'),
            (48, 'Venonat', 'Bug', 'Poison', 60, 55, 50, 40, 55, 45, 305, 31, 'medium-fast'),
            (49, 'Venomoth', 'Bug', 'Poison', 70, 65, 60, 90, 75, 90, 450, None, 'medium-fast'),
            (50, 'Diglett', 'Ground', None, 10, 55, 25, 35, 45, 95, 265, 26, 'medium-fast'),
            (51, 'Dugtrio', 'Ground', None, 35, 100, 50, 50, 70, 120, 425, None, 'medium-fast'),
            (52, 'Meowth', 'Normal', None, 40, 45, 35, 40, 40, 90, 290, 28, 'medium-fast'),
            (53, 'Persian', 'Normal', None, 65, 70, 60, 65, 65, 115, 440, None, 'medium-fast'),
            (54, 'Psyduck', 'Water', None, 50, 52, 48, 65, 50, 55, 320, 33, 'medium-fast'),
            (55, 'Golduck', 'Water', None, 80, 82, 78, 95, 80, 85, 500, None, 'medium-fast'),
            (56, 'Mankey', 'Fighting', None, 40, 80, 35, 35, 45, 70, 305, 28, 'medium-fast'),
            (57, 'Primeape', 'Fighting', None, 65, 105, 60, 60, 70, 95, 455, None, 'medium-fast'),
            (58, 'Growlithe', 'Fire', None, 55, 70, 45, 70, 50, 60, 350, None, 'slow'),
            (59, 'Arcanine', 'Fire', None, 90, 110, 80, 100, 80, 95, 555, None, 'slow'),
            (60, 'Poliwag', 'Water', None, 40, 50, 40, 40, 40, 90, 300, 25, 'medium-slow'),
            (61, 'Poliwhirl', 'Water', None, 65, 65, 65, 50, 50, 90, 385, None, 'medium-slow'),
            (62, 'Poliwrath', 'Water', 'Fighting', 90, 95, 95, 70, 90, 70, 510, None, 'medium-slow'),
            (63, 'Abra', 'Psychic', None, 25, 20, 15, 105, 55, 90, 310, 16, 'medium-slow'),
            (64, 'Kadabra', 'Psychic', None, 40, 35, 30, 120, 70, 105, 400, None, 'medium-slow'),
            (65, 'Alakazam', 'Psychic', None, 55, 50, 45, 135, 95, 120, 500, None, 'medium-slow'),
            (66, 'Machop', 'Fighting', None, 70, 80, 50, 35, 35, 35, 305, 28, 'medium-slow'),
            (67, 'Machoke', 'Fighting', None, 80, 100, 70, 50, 60, 45, 405, None, 'medium-slow'),
            (68, 'Machamp', 'Fighting', None, 90, 130, 80, 65, 85, 55, 505, None, 'medium-slow'),
            (69, 'Bellsprout', 'Grass', 'Poison', 50, 75, 35, 70, 30, 40, 300, 21, 'medium-slow'),
            (70, 'Weepinbell', 'Grass', 'Poison', 65, 90, 50, 85, 45, 55, 390, None, 'medium-slow'),
            (71, 'Victreebel', 'Grass', 'Poison', 80, 105, 65, 100, 70, 70, 490, None, 'medium-slow'),
            (72, 'Tentacool', 'Water', 'Poison', 40, 40, 35, 50, 100, 70, 335, 30, 'slow'),
            (73, 'Tentacruel', 'Water', 'Poison', 80, 70, 65, 80, 120, 100, 515, None, 'slow'),
            (74, 'Geodude', 'Rock', 'Ground', 40, 80, 100, 30, 30, 20, 300, 25, 'medium-slow'),
            (75, 'Graveler', 'Rock', 'Ground', 55, 95, 115, 45, 45, 35, 390, None, 'medium-slow'),
            (76, 'Golem', 'Rock', 'Ground', 80, 120, 130, 55, 65, 45, 495, None, 'medium-slow'),
            (77, 'Ponyta', 'Fire', None, 50, 85, 55, 65, 65, 90, 410, 40, 'medium-fast'),
            (78, 'Rapidash', 'Fire', None, 65, 100, 70, 80, 80, 105, 500, None, 'medium-fast'),
            (79, 'Slowpoke', 'Water', 'Psychic', 90, 65, 65, 40, 40, 15, 315, 37, 'medium-fast'),
            (80, 'Slowbro', 'Water', 'Psychic', 95, 75, 110, 100, 80, 30, 490, None, 'medium-fast'),
            (81, 'Magnemite', 'Electric', 'Steel', 25, 35, 70, 95, 55, 45, 325, 30, 'medium-fast'),
            (82, 'Magneton', 'Electric', 'Steel', 50, 60, 95, 120, 70, 70, 465, None, 'medium-fast'),
            (83, 'Farfetch''d', 'Normal', 'Flying', 52, 90, 55, 58, 62, 60, 377, None, 'medium-fast'),
            (84, 'Doduo', 'Normal', 'Flying', 35, 85, 45, 35, 35, 75, 310, 31, 'medium-fast'),
            (85, 'Dodrio', 'Normal', 'Flying', 60, 110, 70, 60, 60, 110, 470, None, 'medium-fast'),
            (86, 'Seel', 'Water', None, 65, 45, 55, 45, 70, 45, 325, 34, 'medium-fast'),
            (87, 'Dewgong', 'Water', 'Ice', 90, 70, 80, 70, 95, 70, 475, None, 'medium-fast'),
            (88, 'Grimer', 'Poison', None, 80, 80, 50, 40, 50, 25, 325, 38, 'medium-fast'),
            (89, 'Muk', 'Poison', None, 105, 105, 75, 65, 100, 50, 500, None, 'medium-fast'),
            (90, 'Shellder', 'Water', None, 30, 65, 100, 45, 25, 40, 305, None, 'slow'),
            (91, 'Cloyster', 'Water', 'Ice', 50, 95, 180, 85, 45, 70, 525, None, 'slow'),
            (92, 'Gastly', 'Ghost', 'Poison', 30, 35, 30, 100, 35, 80, 310, 25, 'medium-slow'),
            (93, 'Haunter', 'Ghost', 'Poison', 45, 50, 45, 115, 55, 95, 405, None, 'medium-slow'),
            (94, 'Gengar', 'Ghost', 'Poison', 60, 65, 60, 130, 75, 110, 500, None, 'medium-slow'),
            (95, 'Onix', 'Rock', 'Ground', 35, 45, 160, 30, 45, 70, 385, None, 'medium-fast'),
            (96, 'Drowzee', 'Psychic', None, 60, 48, 45, 43, 90, 42, 328, 26, 'medium-fast'),
            (97, 'Hypno', 'Psychic', None, 85, 73, 70, 73, 115, 67, 483, None, 'medium-fast'),
            (98, 'Krabby', 'Water', None, 30, 105, 90, 25, 25, 50, 325, 28, 'medium-fast'),
            (99, 'Kingler', 'Water', None, 55, 130, 115, 50, 50, 75, 475, None, 'medium-fast'),
            (100, 'Voltorb', 'Electric', None, 40, 30, 50, 55, 55, 100, 330, 30, 'medium-fast'),
            (101, 'Electrode', 'Electric', None, 60, 50, 70, 80, 80, 150, 490, None, 'medium-fast'),
            (102, 'Exeggcute', 'Grass', 'Psychic', 60, 40, 80, 60, 45, 40, 325, None, 'slow'),
            (103, 'Exeggutor', 'Grass', 'Psychic', 95, 95, 85, 125, 75, 55, 530, None, 'slow'),
            (104, 'Cubone', 'Ground', None, 50, 50, 95, 40, 50, 35, 320, 28, 'medium-fast'),
            (105, 'Marowak', 'Ground', None, 60, 80, 110, 50, 80, 45, 425, None, 'medium-fast'),
            (106, 'Hitmonlee', 'Fighting', None, 50, 120, 53, 35, 110, 87, 455, None, 'medium-fast'),
            (107, 'Hitmonchan', 'Fighting', None, 50, 105, 79, 35, 110, 76, 455, None, 'medium-fast'),
            (108, 'Lickitung', 'Normal', None, 90, 55, 75, 60, 75, 30, 385, None, 'medium-fast'),
            (109, 'Koffing', 'Poison', None, 40, 65, 95, 60, 45, 35, 340, 35, 'medium-fast'),
            (110, 'Weezing', 'Poison', None, 65, 90, 120, 85, 70, 60, 490, None, 'medium-fast'),
            (111, 'Rhyhorn', 'Ground', 'Rock', 80, 85, 95, 30, 30, 25, 345, 42, 'slow'),
            (112, 'Rhydon', 'Ground', 'Rock', 105, 130, 120, 45, 45, 40, 485, None, 'slow'),
            (113, 'Chansey', 'Normal', None, 250, 5, 5, 35, 105, 50, 450, None, 'fast'),
            (114, 'Tangela', 'Grass', None, 65, 55, 115, 100, 40, 60, 435, None, 'medium-fast'),
            (115, 'Kangaskhan', 'Normal', None, 105, 95, 80, 40, 80, 90, 490, None, 'medium-fast'),
            (116, 'Horsea', 'Water', None, 30, 40, 70, 70, 25, 60, 295, 32, 'medium-fast'),
            (117, 'Seadra', 'Water', None, 55, 65, 95, 95, 45, 85, 440, None, 'medium-fast'),
            (118, 'Goldeen', 'Water', None, 45, 67, 60, 35, 50, 63, 320, 33, 'medium-fast'),
            (119, 'Seaking', 'Water', None, 80, 92, 65, 65, 80, 68, 450, None, 'medium-fast'),
            (120, 'Staryu', 'Water', None, 30, 45, 55, 70, 55, 85, 340, None, 'slow'),
            (121, 'Starmie', 'Water', 'Psychic', 60, 75, 85, 100, 85, 115, 520, None, 'slow'),
            (122, 'Mr. Mime', 'Psychic', 'Fairy', 40, 45, 65, 100, 120, 90, 460, None, 'medium-fast'),
            (123, 'Scyther', 'Bug', 'Flying', 70, 110, 80, 55, 80, 105, 500, None, 'medium-fast'),
            (124, 'Jynx', 'Ice', 'Psychic', 65, 50, 35, 115, 95, 95, 455, None, 'medium-fast'),
            (125, 'Electabuzz', 'Electric', None, 65, 83, 57, 95, 85, 105, 490, None, 'medium-fast'),
            (126, 'Magmar', 'Fire', None, 65, 95, 57, 100, 85, 93, 495, None, 'medium-fast'),
            (127, 'Pinsir', 'Bug', None, 65, 125, 100, 55, 70, 85, 500, None, 'slow'),
            (128, 'Tauros', 'Normal', None, 75, 100, 95, 40, 70, 110, 490, None, 'slow'),
            (129, 'Magikarp', 'Water', None, 20, 10, 55, 15, 20, 80, 200, 20, 'slow'),
            (130, 'Gyarados', 'Water', 'Flying', 95, 125, 79, 60, 100, 81, 540, None, 'slow'),
            (131, 'Lapras', 'Water', 'Ice', 130, 85, 80, 85, 95, 60, 535, None, 'slow'),
            (132, 'Ditto', 'Normal', None, 48, 48, 48, 48, 48, 48, 288, None, 'medium-fast'),
            (133, 'Eevee', 'Normal', None, 55, 55, 50, 45, 65, 55, 325, None, 'medium-fast'),
            (134, 'Vaporeon', 'Water', None, 130, 65, 60, 110, 95, 65, 525, None, 'medium-fast'),
            (135, 'Jolteon', 'Electric', None, 65, 65, 60, 110, 95, 130, 525, None, 'medium-fast'),
            (136, 'Flareon', 'Fire', None, 65, 130, 60, 95, 110, 65, 525, None, 'medium-fast'),
            (137, 'Porygon', 'Normal', None, 65, 60, 70, 85, 75, 40, 395, None, 'medium-fast'),
            (138, 'Omanyte', 'Rock', 'Water', 35, 40, 100, 90, 55, 35, 355, 40, 'medium-fast'),
            (139, 'Omastar', 'Rock', 'Water', 70, 60, 125, 115, 70, 55, 495, None, 'medium-fast'),
            (140, 'Kabuto', 'Rock', 'Water', 30, 80, 90, 55, 45, 55, 355, 40, 'medium-fast'),
            (141, 'Kabutops', 'Rock', 'Water', 60, 115, 105, 65, 70, 80, 495, None, 'medium-fast'),
            (142, 'Aerodactyl', 'Rock', 'Flying', 80, 105, 65, 60, 75, 130, 515, None, 'slow'),
            (143, 'Snorlax', 'Normal', None, 160, 110, 65, 65, 110, 30, 540, None, 'slow'),
            (144, 'Articuno', 'Ice', 'Flying', 90, 85, 100, 95, 125, 85, 580, None, 'slow'),
            (145, 'Zapdos', 'Electric', 'Flying', 90, 90, 85, 125, 90, 100, 580, None, 'slow'),
            (146, 'Moltres', 'Fire', 'Flying', 90, 100, 90, 125, 85, 90, 580, None, 'slow'),
            (147, 'Dratini', 'Dragon', None, 41, 64, 45, 50, 50, 50, 300, 30, 'slow'),
            (148, 'Dragonair', 'Dragon', None, 61, 84, 65, 70, 70, 70, 420, 55, 'slow'),
            (149, 'Dragonite', 'Dragon', 'Flying', 91, 134, 95, 100, 100, 80, 600, None, 'slow'),
            (150, 'Mewtwo', 'Psychic', None, 106, 110, 90, 154, 90, 130, 680, None, 'slow'),
            (151, 'Mew', 'Psychic', None, 100, 100, 100, 100, 100, 100, 600, None, 'medium-slow')
        ]
        
        # Clear the table first to avoid duplicates
        cursor.execute("DELETE FROM pokemon")
        
        # Insert all Pokémon with their evolution levels and exp curves
        cursor.executemany('''
        INSERT INTO pokemon 
        (id, name, type1, type2, hp, attack, defense, special_attack, special_defense, speed, total_stats, evolution_level, exp_curve)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pokemon_data)
        
        print(f"Successfully inserted {len(pokemon_data)} Pokemon")

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
    
    # First initialize the base database with all tables
    print("Initializing base database...")
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    print("✅ Base database initialized")
    
    # Then add Pokémon data
    print("\nAdding Pokémon data...")
    pokemon_db = PokemonDataManager()
    pokemon_db.initialize_pokemon_data()
    
    # Verify data was inserted
    pokemon_count = len(get_all_pokemon())
    print(f"\n✅ Total Pokémon in database: {pokemon_count}")

if __name__ == "__main__":
    main()