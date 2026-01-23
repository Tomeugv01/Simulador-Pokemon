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
    
    def initialize_pokemon_data(self, include_gen5_6=True):
        """Insert all Pokémon, their learnsets, and evolution data
        
        Args:
            include_gen5_6: If True, also inserts Gen 5-6 Pokemon (IDs 494-721)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Insert all Pokémon
        print("Inserting Pokémon data (Gen 1-4)...")
        self._insert_pokemon(cursor)
        
        # Optionally insert Gen 5-6 Pokemon
        if include_gen5_6:
            print("Inserting Gen 5-6 Pokémon...")
            self._insert_gen5_6_pokemon(cursor)
        
        # Insert learnsets
        print("Inserting pokemon learnsets...")
        self._insert_pokemon_learnsets(cursor)
        
        # Insert evolutions
        print("Inserting pokemon evolutions...")
        self._insert_pokemon_evolutions(cursor)
        
        # Insert abilities
        print("Inserting abilities...")
        self._insert_abilities(cursor)
        
        conn.commit()
        conn.close()
        print("✅ Pokemon data initialized successfully!")

    def _insert_pokemon(self, cursor):
        """Insert all Pokémon through Generation 4 with their statistics, evolution levels and exp curves"""
        pokemon_data = [
            # Generation 1 (1-151) - You already have most of these, but I'll include for completeness
            # Type IDs: 1=Normal, 2=Fire, 3=Water, 4=Electric, 5=Grass, 6=Ice, 7=Fighting, 8=Poison, 9=Ground, 10=Flying, 
            # 11=Psychic, 12=Bug, 13=Rock, 14=Ghost, 15=Dragon, 16=Dark, 17=Steel, 18=Fairy
            (1, 'Bulbasaur', 5, 8, 45, 49, 49, 65, 65, 45, 318, 16, 'medium-slow'),
            (2, 'Ivysaur', 5, 8, 60, 62, 63, 80, 80, 60, 405, 32, 'medium-slow'),
            (3, 'Venusaur', 5, 8, 80, 82, 83, 100, 100, 80, 525, None, 'medium-slow'),
            (4, 'Charmander', 2, None, 39, 52, 43, 60, 50, 65, 309, 16, 'medium-slow'),
            (5, 'Charmeleon', 2, None, 58, 64, 58, 80, 65, 80, 405, 36, 'medium-slow'),
            (6, 'Charizard', 2, 10, 78, 84, 78, 109, 85, 100, 534, None, 'medium-slow'),
            (7, 'Squirtle', 3, None, 44, 48, 65, 50, 64, 43, 314, 16, 'medium-slow'),
            (8, 'Wartortle', 3, None, 59, 63, 80, 65, 80, 58, 405, 36, 'medium-slow'),
            (9, 'Blastoise', 3, None, 79, 83, 100, 85, 105, 78, 530, None, 'medium-slow'),
            (10, 'Caterpie', 12, None, 45, 30, 35, 20, 20, 45, 195, 7, 'medium-fast'),
            (11, 'Metapod', 12, None, 50, 20, 55, 25, 25, 30, 205, 10, 'medium-fast'),
            (12, 'Butterfree', 12, 10, 60, 45, 50, 90, 80, 70, 395, None, 'medium-fast'),
            (13, 'Weedle', 12, 8, 40, 35, 30, 20, 20, 50, 195, 7, 'medium-fast'),
            (14, 'Kakuna', 12, 8, 45, 25, 50, 25, 25, 35, 205, 10, 'medium-fast'),
            (15, 'Beedrill', 12, 8, 65, 90, 40, 45, 80, 75, 395, None, 'medium-fast'),
            (16, 'Pidgey', 1, 10, 40, 45, 40, 35, 35, 56, 251, 18, 'medium-fast'),
            (17, 'Pidgeotto', 1, 10, 63, 60, 55, 50, 50, 71, 349, 36, 'medium-fast'),
            (18, 'Pidgeot', 1, 10, 83, 80, 75, 70, 70, 101, 479, None, 'medium-fast'),
            (19, 'Rattata', 1, None, 30, 56, 35, 25, 35, 72, 253, 20, 'medium-fast'),
            (20, 'Raticate', 1, None, 55, 81, 60, 50, 70, 97, 413, None, 'medium-fast'),
            (21, 'Spearow', 1, 10, 40, 60, 30, 31, 31, 70, 262, 20, 'medium-fast'),
            (22, 'Fearow', 1, 10, 65, 90, 65, 61, 61, 100, 442, None, 'medium-fast'),
            (23, 'Ekans', 8, None, 35, 60, 44, 40, 54, 55, 288, 22, 'medium-fast'),
            (24, 'Arbok', 8, None, 60, 95, 69, 65, 79, 80, 448, None, 'medium-fast'),
            (25, 'Pikachu', 4, None, 35, 55, 40, 50, 50, 90, 320, None, 'medium-fast'),
            (26, 'Raichu', 4, None, 60, 90, 55, 90, 80, 110, 485, None, 'medium-fast'),
            (27, 'Sandshrew', 9, None, 50, 75, 85, 20, 30, 40, 300, 22, 'medium-fast'),
            (28, 'Sandslash', 9, None, 75, 100, 110, 45, 55, 65, 450, None, 'medium-fast'),
            (29, 'Nidoran♀', 8, None, 55, 47, 52, 40, 40, 41, 275, 16, 'medium-slow'),
            (30, 'Nidorina', 8, None, 70, 62, 67, 55, 55, 56, 365, None, 'medium-slow'),
            (31, 'Nidoqueen', 8, 9, 90, 92, 87, 75, 85, 76, 505, None, 'medium-slow'),
            (32, 'Nidoran♂', 8, None, 46, 57, 40, 40, 40, 50, 273, 16, 'medium-slow'),
            (33, 'Nidorino', 8, None, 61, 72, 57, 55, 55, 65, 365, None, 'medium-slow'),
            (34, 'Nidoking', 8, 9, 81, 102, 77, 85, 75, 85, 505, None, 'medium-slow'),
            (35, 'Clefairy', 18, None, 70, 45, 48, 60, 65, 35, 323, None, 'fast'),
            (36, 'Clefable', 18, None, 95, 70, 73, 95, 90, 60, 483, None, 'fast'),
            (37, 'Vulpix', 2, None, 38, 41, 40, 50, 65, 65, 299, None, 'medium-fast'),
            (38, 'Ninetales', 2, None, 73, 76, 75, 81, 100, 100, 505, None, 'medium-fast'),
            (39, 'Jigglypuff', 1, 18, 115, 45, 20, 45, 25, 20, 270, None, 'fast'),
            (40, 'Wigglytuff', 1, 18, 140, 70, 45, 85, 50, 45, 435, None, 'fast'),
            (41, 'Zubat', 8, 10, 40, 45, 35, 30, 40, 55, 245, 22, 'medium-fast'),
            (42, 'Golbat', 8, 10, 75, 80, 70, 65, 75, 90, 455, None, 'medium-fast'),
            (43, 'Oddish', 5, 8, 45, 50, 55, 75, 65, 30, 320, 21, 'medium-slow'),
            (44, 'Gloom', 5, 8, 60, 65, 70, 85, 75, 40, 395, None, 'medium-slow'),
            (45, 'Vileplume', 5, 8, 75, 80, 85, 110, 90, 50, 490, None, 'medium-slow'),
            (46, 'Paras', 12, 5, 35, 70, 55, 45, 55, 25, 285, 24, 'medium-fast'),
            (47, 'Parasect', 12, 5, 60, 95, 80, 60, 80, 30, 405, None, 'medium-fast'),
            (48, 'Venonat', 12, 8, 60, 55, 50, 40, 55, 45, 305, 31, 'medium-fast'),
            (49, 'Venomoth', 12, 8, 70, 65, 60, 90, 75, 90, 450, None, 'medium-fast'),
            (50, 'Diglett', 9, None, 10, 55, 25, 35, 45, 95, 265, 26, 'medium-fast'),
            (51, 'Dugtrio', 9, None, 35, 100, 50, 50, 70, 120, 425, None, 'medium-fast'),
            (52, 'Meowth', 1, None, 40, 45, 35, 40, 40, 90, 290, 28, 'medium-fast'),
            (53, 'Persian', 1, None, 65, 70, 60, 65, 65, 115, 440, None, 'medium-fast'),
            (54, 'Psyduck', 3, None, 50, 52, 48, 65, 50, 55, 320, 33, 'medium-fast'),
            (55, 'Golduck', 3, None, 80, 82, 78, 95, 80, 85, 500, None, 'medium-fast'),
            (56, 'Mankey', 7, None, 40, 80, 35, 35, 45, 70, 305, 28, 'medium-fast'),
            (57, 'Primeape', 7, None, 65, 105, 60, 60, 70, 95, 455, None, 'medium-fast'),
            (58, 'Growlithe', 2, None, 55, 70, 45, 70, 50, 60, 350, None, 'slow'),
            (59, 'Arcanine', 2, None, 90, 110, 80, 100, 80, 95, 555, None, 'slow'),
            (60, 'Poliwag', 3, None, 40, 50, 40, 40, 40, 90, 300, 25, 'medium-slow'),
            (61, 'Poliwhirl', 3, None, 65, 65, 65, 50, 50, 90, 385, None, 'medium-slow'),
            (62, 'Poliwrath', 3, 7, 90, 95, 95, 70, 90, 70, 510, None, 'medium-slow'),
            (63, 'Abra', 11, None, 25, 20, 15, 105, 55, 90, 310, 16, 'medium-slow'),
            (64, 'Kadabra', 11, None, 40, 35, 30, 120, 70, 105, 400, None, 'medium-slow'),
            (65, 'Alakazam', 11, None, 55, 50, 45, 135, 95, 120, 500, None, 'medium-slow'),
            (66, 'Machop', 7, None, 70, 80, 50, 35, 35, 35, 305, 28, 'medium-slow'),
            (67, 'Machoke', 7, None, 80, 100, 70, 50, 60, 45, 405, None, 'medium-slow'),
            (68, 'Machamp', 7, None, 90, 130, 80, 65, 85, 55, 505, None, 'medium-slow'),
            (69, 'Bellsprout', 5, 8, 50, 75, 35, 70, 30, 40, 300, 21, 'medium-slow'),
            (70, 'Weepinbell', 5, 8, 65, 90, 50, 85, 45, 55, 390, None, 'medium-slow'),
            (71, 'Victreebel', 5, 8, 80, 105, 65, 100, 70, 70, 490, None, 'medium-slow'),
            (72, 'Tentacool', 3, 8, 40, 40, 35, 50, 100, 70, 335, 30, 'slow'),
            (73, 'Tentacruel', 3, 8, 80, 70, 65, 80, 120, 100, 515, None, 'slow'),
            (74, 'Geodude', 13, 9, 40, 80, 100, 30, 30, 20, 300, 25, 'medium-slow'),
            (75, 'Graveler', 13, 9, 55, 95, 115, 45, 45, 35, 390, None, 'medium-slow'),
            (76, 'Golem', 13, 9, 80, 120, 130, 55, 65, 45, 495, None, 'medium-slow'),
            (77, 'Ponyta', 2, None, 50, 85, 55, 65, 65, 90, 410, 40, 'medium-fast'),
            (78, 'Rapidash', 2, None, 65, 100, 70, 80, 80, 105, 500, None, 'medium-fast'),
            (79, 'Slowpoke', 3, 11, 90, 65, 65, 40, 40, 15, 315, 37, 'medium-fast'),
            (80, 'Slowbro', 3, 11, 95, 75, 110, 100, 80, 30, 490, None, 'medium-fast'),
            (81, 'Magnemite', 4, 17, 25, 35, 70, 95, 55, 45, 325, 30, 'medium-fast'),
            (82, 'Magneton', 4, 17, 50, 60, 95, 120, 70, 70, 465, None, 'medium-fast'),
            (83, "Farfetch'd", 1, 10, 52, 90, 55, 58, 62, 60, 377, None, 'medium-fast'),
            (84, 'Doduo', 1, 10, 35, 85, 45, 35, 35, 75, 310, 31, 'medium-fast'),
            (85, 'Dodrio', 1, 10, 60, 110, 70, 60, 60, 110, 470, None, 'medium-fast'),
            (86, 'Seel', 3, None, 65, 45, 55, 45, 70, 45, 325, 34, 'medium-fast'),
            (87, 'Dewgong', 3, 6, 90, 70, 80, 70, 95, 70, 475, None, 'medium-fast'),
            (88, 'Grimer', 8, None, 80, 80, 50, 40, 50, 25, 325, 38, 'medium-fast'),
            (89, 'Muk', 8, None, 105, 105, 75, 65, 100, 50, 500, None, 'medium-fast'),
            (90, 'Shellder', 3, None, 30, 65, 100, 45, 25, 40, 305, None, 'slow'),
            (91, 'Cloyster', 3, 6, 50, 95, 180, 85, 45, 70, 525, None, 'slow'),
            (92, 'Gastly', 14, 8, 30, 35, 30, 100, 35, 80, 310, 25, 'medium-slow'),
            (93, 'Haunter', 14, 8, 45, 50, 45, 115, 55, 95, 405, None, 'medium-slow'),
            (94, 'Gengar', 14, 8, 60, 65, 60, 130, 75, 110, 500, None, 'medium-slow'),
            (95, 'Onix', 13, 9, 35, 45, 160, 30, 45, 70, 385, None, 'medium-fast'),
            (96, 'Drowzee', 11, None, 60, 48, 45, 43, 90, 42, 328, 26, 'medium-fast'),
            (97, 'Hypno', 11, None, 85, 73, 70, 73, 115, 67, 483, None, 'medium-fast'),
            (98, 'Krabby', 3, None, 30, 105, 90, 25, 25, 50, 325, 28, 'medium-fast'),
            (99, 'Kingler', 3, None, 55, 130, 115, 50, 50, 75, 475, None, 'medium-fast'),
            (100, 'Voltorb', 4, None, 40, 30, 50, 55, 55, 100, 330, 30, 'medium-fast'),
            (101, 'Electrode', 4, None, 60, 50, 70, 80, 80, 150, 490, None, 'medium-fast'),
            (102, 'Exeggcute', 5, 11, 60, 40, 80, 60, 45, 40, 325, None, 'slow'),
            (103, 'Exeggutor', 5, 11, 95, 95, 85, 125, 75, 55, 530, None, 'slow'),
            (104, 'Cubone', 9, None, 50, 50, 95, 40, 50, 35, 320, 28, 'medium-fast'),
            (105, 'Marowak', 9, None, 60, 80, 110, 50, 80, 45, 425, None, 'medium-fast'),
            (106, 'Hitmonlee', 7, None, 50, 120, 53, 35, 110, 87, 455, None, 'medium-fast'),
            (107, 'Hitmonchan', 7, None, 50, 105, 79, 35, 110, 76, 455, None, 'medium-fast'),
            (108, 'Lickitung', 1, None, 90, 55, 75, 60, 75, 30, 385, None, 'medium-fast'),
            (109, 'Koffing', 8, None, 40, 65, 95, 60, 45, 35, 340, 35, 'medium-fast'),
            (110, 'Weezing', 8, None, 65, 90, 120, 85, 70, 60, 490, None, 'medium-fast'),
            (111, 'Rhyhorn', 9, 13, 80, 85, 95, 30, 30, 25, 345, 42, 'slow'),
            (112, 'Rhydon', 9, 13, 105, 130, 120, 45, 45, 40, 485, None, 'slow'),
            (113, 'Chansey', 1, None, 250, 5, 5, 35, 105, 50, 450, None, 'fast'),
            (114, 'Tangela', 5, None, 65, 55, 115, 100, 40, 60, 435, None, 'medium-fast'),
            (115, 'Kangaskhan', 1, None, 105, 95, 80, 40, 80, 90, 490, None, 'medium-fast'),
            (116, 'Horsea', 3, None, 30, 40, 70, 70, 25, 60, 295, 32, 'medium-fast'),
            (117, 'Seadra', 3, None, 55, 65, 95, 95, 45, 85, 440, None, 'medium-fast'),
            (118, 'Goldeen', 3, None, 45, 67, 60, 35, 50, 63, 320, 33, 'medium-fast'),
            (119, 'Seaking', 3, None, 80, 92, 65, 65, 80, 68, 450, None, 'medium-fast'),
            (120, 'Staryu', 3, None, 30, 45, 55, 70, 55, 85, 340, None, 'slow'),
            (121, 'Starmie', 3, 11, 60, 75, 85, 100, 85, 115, 520, None, 'slow'),
            (122, 'Mr. Mime', 11, 18, 40, 45, 65, 100, 120, 90, 460, None, 'medium-fast'),
            (123, 'Scyther', 12, 10, 70, 110, 80, 55, 80, 105, 500, None, 'medium-fast'),
            (124, 'Jynx', 6, 11, 65, 50, 35, 115, 95, 95, 455, None, 'medium-fast'),
            (125, 'Electabuzz', 4, None, 65, 83, 57, 95, 85, 105, 490, None, 'medium-fast'),
            (126, 'Magmar', 2, None, 65, 95, 57, 100, 85, 93, 495, None, 'medium-fast'),
            (127, 'Pinsir', 12, None, 65, 125, 100, 55, 70, 85, 500, None, 'slow'),
            (128, 'Tauros', 1, None, 75, 100, 95, 40, 70, 110, 490, None, 'slow'),
            (129, 'Magikarp', 3, None, 20, 10, 55, 15, 20, 80, 200, 20, 'slow'),
            (130, 'Gyarados', 3, 10, 95, 125, 79, 60, 100, 81, 540, None, 'slow'),
            (131, 'Lapras', 3, 6, 130, 85, 80, 85, 95, 60, 535, None, 'slow'),
            (132, 'Ditto', 1, None, 48, 48, 48, 48, 48, 48, 288, None, 'medium-fast'),
            (133, 'Eevee', 1, None, 55, 55, 50, 45, 65, 55, 325, None, 'medium-fast'),
            (134, 'Vaporeon', 3, None, 130, 65, 60, 110, 95, 65, 525, None, 'medium-fast'),
            (135, 'Jolteon', 4, None, 65, 65, 60, 110, 95, 130, 525, None, 'medium-fast'),
            (136, 'Flareon', 2, None, 65, 130, 60, 95, 110, 65, 525, None, 'medium-fast'),
            (137, 'Porygon', 1, None, 65, 60, 70, 85, 75, 40, 395, None, 'medium-fast'),
            (138, 'Omanyte', 13, 3, 35, 40, 100, 90, 55, 35, 355, 40, 'medium-fast'),
            (139, 'Omastar', 13, 3, 70, 60, 125, 115, 70, 55, 495, None, 'medium-fast'),
            (140, 'Kabuto', 13, 3, 30, 80, 90, 55, 45, 55, 355, 40, 'medium-fast'),
            (141, 'Kabutops', 13, 3, 60, 115, 105, 65, 70, 80, 495, None, 'medium-fast'),
            (142, 'Aerodactyl', 13, 10, 80, 105, 65, 60, 75, 130, 515, None, 'slow'),
            (143, 'Snorlax', 1, None, 160, 110, 65, 65, 110, 30, 540, None, 'slow'),
            (144, 'Articuno', 6, 10, 90, 85, 100, 95, 125, 85, 580, None, 'slow'),
            (145, 'Zapdos', 4, 10, 90, 90, 85, 125, 90, 100, 580, None, 'slow'),
            (146, 'Moltres', 2, 10, 90, 100, 90, 125, 85, 90, 580, None, 'slow'),
            (147, 'Dratini', 15, None, 41, 64, 45, 50, 50, 50, 300, 30, 'slow'),
            (148, 'Dragonair', 15, None, 61, 84, 65, 70, 70, 70, 420, 55, 'slow'),
            (149, 'Dragonite', 15, 10, 91, 134, 95, 100, 100, 80, 600, None, 'slow'),
            (150, 'Mewtwo', 11, None, 106, 110, 90, 154, 90, 130, 680, None, 'slow'),
            (151, 'Mew', 11, None, 100, 100, 100, 100, 100, 100, 600, None, 'medium-slow'),
            
            # Generation 2 (152-251)
            (152, 'Chikorita', 5, None, 45, 49, 65, 49, 65, 45, 318, 16, 'medium-slow'),
            (153, 'Bayleef', 5, None, 60, 62, 80, 63, 80, 60, 405, 32, 'medium-slow'),
            (154, 'Meganium', 5, None, 80, 82, 100, 83, 100, 80, 525, None, 'medium-slow'),
            (155, 'Cyndaquil', 2, None, 39, 52, 43, 60, 50, 65, 309, 14, 'medium-slow'),
            (156, 'Quilava', 2, None, 58, 64, 58, 80, 65, 80, 405, 36, 'medium-slow'),
            (157, 'Typhlosion', 2, None, 78, 84, 78, 109, 85, 100, 534, None, 'medium-slow'),
            (158, 'Totodile', 3, None, 50, 65, 64, 44, 48, 43, 314, 18, 'medium-slow'),
            (159, 'Croconaw', 3, None, 65, 80, 80, 59, 63, 58, 405, 30, 'medium-slow'),
            (160, 'Feraligatr', 3, None, 85, 105, 100, 79, 83, 78, 530, None, 'medium-slow'),
            (161, 'Sentret', 1, None, 35, 46, 34, 35, 45, 20, 215, 15, 'medium-fast'),
            (162, 'Furret', 1, None, 85, 76, 64, 45, 55, 90, 415, None, 'medium-fast'),
            (163, 'Hoothoot', 1, 10, 60, 30, 30, 36, 56, 50, 262, 20, 'medium-fast'),
            (164, 'Noctowl', 1, 10, 100, 50, 50, 86, 96, 70, 452, None, 'medium-fast'),
            (165, 'Ledyba', 12, 10, 40, 20, 30, 40, 80, 55, 265, 18, 'fast'),
            (166, 'Ledian', 12, 10, 55, 35, 50, 55, 110, 85, 390, None, 'fast'),
            (167, 'Spinarak', 12, 8, 40, 60, 40, 40, 40, 30, 250, 22, 'fast'),
            (168, 'Ariados', 12, 8, 70, 90, 70, 60, 70, 40, 400, None, 'fast'),
            (169, 'Crobat', 8, 10, 85, 90, 80, 70, 80, 130, 535, None, 'medium-fast'),
            (170, 'Chinchou', 3, 4, 75, 38, 38, 56, 56, 67, 330, 27, 'slow'),
            (171, 'Lanturn', 3, 4, 125, 58, 58, 76, 76, 67, 460, None, 'slow'),
            (172, 'Pichu', 4, None, 20, 40, 15, 35, 35, 60, 205, None, 'medium-fast'),
            (173, 'Cleffa', 18, None, 50, 25, 28, 45, 55, 15, 218, None, 'fast'),
            (174, 'Igglybuff', 1, 18, 90, 30, 15, 40, 20, 15, 210, None, 'fast'),
            (175, 'Togepi', 18, None, 35, 20, 65, 40, 65, 20, 245, None, 'fast'),
            (176, 'Togetic', 18, 10, 55, 40, 85, 80, 105, 40, 405, None, 'fast'),
            (177, 'Natu', 11, 10, 40, 50, 45, 70, 45, 70, 320, 25, 'medium-fast'),
            (178, 'Xatu', 11, 10, 65, 75, 70, 95, 70, 95, 470, None, 'medium-fast'),
            (179, 'Mareep', 4, None, 55, 40, 40, 65, 45, 35, 280, 15, 'medium-slow'),
            (180, 'Flaaffy', 4, None, 70, 55, 55, 80, 60, 45, 365, 30, 'medium-slow'),
            (181, 'Ampharos', 4, None, 90, 75, 85, 115, 90, 55, 510, None, 'medium-slow'),
            (182, 'Bellossom', 5, None, 75, 80, 95, 90, 100, 50, 490, None, 'medium-slow'),
            (183, 'Marill', 3, 18, 70, 20, 50, 20, 50, 40, 250, 18, 'fast'),
            (184, 'Azumarill', 3, 18, 100, 50, 80, 60, 80, 50, 420, None, 'fast'),
            (185, 'Sudowoodo', 13, None, 70, 100, 115, 30, 65, 30, 410, None, 'medium-fast'),
            (186, 'Politoed', 3, None, 90, 75, 75, 90, 100, 70, 500, None, 'medium-slow'),
            (187, 'Hoppip', 5, 10, 35, 35, 40, 35, 55, 50, 250, 18, 'medium-slow'),
            (188, 'Skiploom', 5, 10, 55, 45, 50, 45, 65, 80, 340, 27, 'medium-slow'),
            (189, 'Jumpluff', 5, 10, 75, 55, 70, 55, 95, 110, 460, None, 'medium-slow'),
            (190, 'Aipom', 1, None, 55, 70, 55, 40, 55, 85, 360, None, 'fast'),
            (191, 'Sunkern', 5, None, 30, 30, 30, 30, 30, 30, 180, None, 'medium-slow'),
            (192, 'Sunflora', 5, None, 75, 75, 55, 105, 85, 30, 425, None, 'medium-slow'),
            (193, 'Yanma', 12, 10, 65, 65, 45, 75, 45, 95, 390, None, 'medium-fast'),
            (194, 'Wooper', 3, 9, 55, 45, 45, 25, 25, 15, 210, 20, 'medium-fast'),
            (195, 'Quagsire', 3, 9, 95, 85, 85, 65, 65, 35, 430, None, 'medium-fast'),
            (196, 'Espeon', 11, None, 65, 65, 60, 130, 95, 110, 525, None, 'medium-fast'),
            (197, 'Umbreon', 16, None, 95, 65, 110, 60, 130, 65, 525, None, 'medium-fast'),
            (198, 'Murkrow', 16, 10, 60, 85, 42, 85, 42, 91, 405, None, 'medium-slow'),
            (199, 'Slowking', 3, 11, 95, 75, 80, 100, 110, 30, 490, None, 'medium-fast'),
            (200, 'Misdreavus', 14, None, 60, 60, 60, 85, 85, 85, 435, None, 'fast'),
            (201, 'Unown', 11, None, 48, 72, 48, 72, 48, 48, 336, None, 'medium-fast'),
            (202, 'Wobbuffet', 11, None, 190, 33, 58, 33, 58, 33, 405, None, 'medium-fast'),
            (203, 'Girafarig', 1, 11, 70, 80, 65, 90, 65, 85, 455, None, 'medium-fast'),
            (204, 'Pineco', 12, None, 50, 65, 90, 35, 35, 15, 290, 31, 'medium-fast'),
            (205, 'Forretress', 12, 17, 75, 90, 140, 60, 60, 40, 465, None, 'medium-fast'),
            (206, 'Dunsparce', 1, None, 100, 70, 70, 65, 65, 45, 415, None, 'medium-fast'),
            (207, 'Gligar', 9, 10, 65, 75, 105, 35, 65, 85, 430, None, 'medium-slow'),
            (208, 'Steelix', 17, 9, 75, 85, 200, 55, 65, 30, 510, None, 'medium-fast'),
            (209, 'Snubbull', 18, None, 60, 80, 50, 40, 40, 30, 300, 23, 'fast'),
            (210, 'Granbull', 18, None, 90, 120, 75, 60, 60, 45, 450, None, 'fast'),
            (211, 'Qwilfish', 3, 8, 65, 95, 85, 55, 55, 85, 440, None, 'medium-fast'),
            (212, 'Scizor', 12, 17, 70, 130, 100, 55, 80, 65, 500, None, 'medium-fast'),
            (213, 'Shuckle', 12, 13, 20, 10, 230, 10, 230, 5, 505, None, 'medium-slow'),
            (214, 'Heracross', 12, 7, 80, 125, 75, 40, 95, 85, 500, None, 'slow'),
            (215, 'Sneasel', 16, 6, 55, 95, 55, 35, 75, 115, 430, None, 'medium-slow'),
            (216, 'Teddiursa', 1, None, 60, 80, 50, 50, 50, 40, 330, 30, 'medium-fast'),
            (217, 'Ursaring', 1, None, 90, 130, 75, 75, 75, 55, 500, None, 'medium-fast'),
            (218, 'Slugma', 2, None, 40, 40, 40, 70, 40, 20, 250, 38, 'medium-fast'),
            (219, 'Magcargo', 2, 13, 60, 50, 120, 90, 80, 30, 430, None, 'medium-fast'),
            (220, 'Swinub', 6, 9, 50, 50, 40, 30, 30, 50, 250, 33, 'slow'),
            (221, 'Piloswine', 6, 9, 100, 100, 80, 60, 60, 50, 450, None, 'slow'),
            (222, 'Corsola', 3, 13, 65, 55, 95, 65, 95, 35, 410, None, 'fast'),
            (223, 'Remoraid', 3, None, 35, 65, 35, 65, 35, 65, 300, 25, 'medium-fast'),
            (224, 'Octillery', 3, None, 75, 105, 75, 105, 75, 45, 480, None, 'medium-fast'),
            (225, 'Delibird', 6, 10, 45, 55, 45, 65, 45, 75, 330, None, 'fast'),
            (226, 'Mantine', 3, 10, 85, 40, 70, 80, 140, 70, 485, None, 'slow'),
            (227, 'Skarmory', 17, 10, 65, 80, 140, 40, 70, 70, 465, None, 'slow'),
            (228, 'Houndour', 16, 2, 45, 60, 30, 80, 50, 65, 330, 24, 'slow'),
            (229, 'Houndoom', 16, 2, 75, 90, 50, 110, 80, 95, 500, None, 'slow'),
            (230, 'Kingdra', 3, 15, 75, 95, 95, 95, 95, 85, 540, None, 'medium-fast'),
            (231, 'Phanpy', 9, None, 90, 60, 60, 40, 40, 40, 330, 25, 'medium-fast'),
            (232, 'Donphan', 9, None, 90, 120, 120, 60, 60, 50, 500, None, 'medium-fast'),
            (233, 'Porygon2', 1, None, 85, 80, 90, 105, 95, 60, 515, None, 'medium-fast'),
            (234, 'Stantler', 1, None, 73, 95, 62, 85, 65, 85, 465, None, 'slow'),
            (235, 'Smeargle', 1, None, 55, 20, 35, 20, 45, 75, 250, None, 'fast'),
            (236, 'Tyrogue', 7, None, 35, 35, 35, 35, 35, 35, 210, 20, 'medium-fast'),
            (237, 'Hitmontop', 7, None, 50, 95, 95, 35, 110, 70, 455, None, 'medium-fast'),
            (238, 'Smoochum', 6, 11, 45, 30, 15, 85, 65, 65, 305, 30, 'medium-fast'),
            (239, 'Elekid', 4, None, 45, 63, 37, 65, 55, 95, 360, 30, 'medium-fast'),
            (240, 'Magby', 2, None, 45, 75, 37, 70, 55, 83, 365, 30, 'medium-fast'),
            (241, 'Miltank', 1, None, 95, 80, 105, 40, 70, 100, 490, None, 'slow'),
            (242, 'Blissey', 1, None, 255, 10, 10, 75, 135, 55, 540, None, 'fast'),
            (243, 'Raikou', 4, None, 90, 85, 75, 115, 100, 115, 580, None, 'slow'),
            (244, 'Entei', 2, None, 115, 115, 85, 90, 75, 100, 580, None, 'slow'),
            (245, 'Suicune', 3, None, 100, 75, 115, 90, 115, 85, 580, None, 'slow'),
            (246, 'Larvitar', 13, 9, 50, 64, 50, 45, 50, 41, 300, 30, 'slow'),
            (247, 'Pupitar', 13, 9, 70, 84, 70, 65, 70, 51, 410, 55, 'slow'),
            (248, 'Tyranitar', 13, 16, 100, 134, 110, 95, 100, 61, 600, None, 'slow'),
            (249, 'Lugia', 11, 10, 106, 90, 130, 90, 154, 110, 680, None, 'slow'),
            (250, 'Ho-Oh', 2, 10, 106, 130, 90, 110, 154, 90, 680, None, 'slow'),
            (251, 'Celebi', 11, 5, 100, 100, 100, 100, 100, 100, 600, None, 'medium-slow'),
            
            # Generation 3 (252-386)
            (252, 'Treecko', 5, None, 40, 45, 35, 65, 55, 70, 310, 16, 'medium-slow'),
            (253, 'Grovyle', 5, None, 50, 65, 45, 85, 65, 95, 405, 36, 'medium-slow'),
            (254, 'Sceptile', 5, None, 70, 85, 65, 105, 85, 120, 530, None, 'medium-slow'),
            (255, 'Torchic', 2, None, 45, 60, 40, 70, 50, 45, 310, 16, 'medium-slow'),
            (256, 'Combusken', 2, 7, 60, 85, 60, 85, 60, 55, 405, 36, 'medium-slow'),
            (257, 'Blaziken', 2, 7, 80, 120, 70, 110, 70, 80, 530, None, 'medium-slow'),
            (258, 'Mudkip', 3, None, 50, 70, 50, 50, 50, 40, 310, 16, 'medium-slow'),
            (259, 'Marshtomp', 3, 9, 70, 85, 70, 60, 70, 50, 405, 36, 'medium-slow'),
            (260, 'Swampert', 3, 9, 100, 110, 90, 85, 90, 60, 535, None, 'medium-slow'),
            (261, 'Poochyena', 16, None, 35, 55, 35, 30, 30, 35, 220, 18, 'medium-fast'),
            (262, 'Mightyena', 16, None, 70, 90, 70, 60, 60, 70, 420, None, 'medium-fast'),
            (263, 'Zigzagoon', 1, None, 38, 30, 41, 30, 41, 60, 240, 20, 'medium-fast'),
            (264, 'Linoone', 1, None, 78, 70, 61, 50, 61, 100, 420, None, 'medium-fast'),
            (265, 'Wurmple', 12, None, 45, 45, 35, 20, 30, 20, 195, 7, 'medium-fast'),
            (266, 'Silcoon', 12, None, 50, 35, 55, 25, 25, 15, 205, 10, 'medium-fast'),
            (267, 'Beautifly', 12, 10, 60, 70, 50, 100, 50, 65, 395, None, 'medium-fast'),
            (268, 'Cascoon', 12, None, 50, 35, 55, 25, 25, 15, 205, 10, 'medium-fast'),
            (269, 'Dustox', 12, 8, 60, 50, 70, 50, 90, 65, 385, None, 'medium-fast'),
            (270, 'Lotad', 3, 5, 40, 30, 30, 40, 50, 30, 220, 14, 'medium-slow'),
            (271, 'Lombre', 3, 5, 60, 50, 50, 60, 70, 50, 340, None, 'medium-slow'),
            (272, 'Ludicolo', 3, 5, 80, 70, 70, 90, 100, 70, 480, None, 'medium-slow'),
            (273, 'Seedot', 5, None, 40, 40, 50, 30, 30, 30, 220, 14, 'medium-slow'),
            (274, 'Nuzleaf', 5, 16, 70, 70, 40, 60, 40, 60, 340, None, 'medium-slow'),
            (275, 'Shiftry', 5, 16, 90, 100, 60, 90, 60, 80, 480, None, 'medium-slow'),
            (276, 'Taillow', 1, 10, 40, 55, 30, 30, 30, 85, 270, 22, 'medium-slow'),
            (277, 'Swellow', 1, 10, 60, 85, 60, 75, 50, 125, 455, None, 'medium-slow'),
            (278, 'Wingull', 3, 10, 40, 30, 30, 55, 30, 85, 270, 25, 'medium-fast'),
            (279, 'Pelipper', 3, 10, 60, 50, 100, 95, 70, 65, 440, None, 'medium-fast'),
            (280, 'Ralts', 11, 18, 28, 25, 25, 45, 35, 40, 198, 20, 'slow'),
            (281, 'Kirlia', 11, 18, 38, 35, 35, 65, 55, 50, 278, 30, 'slow'),
            (282, 'Gardevoir', 11, 18, 68, 65, 65, 125, 115, 80, 518, None, 'slow'),
            (283, 'Surskit', 12, 3, 40, 30, 32, 50, 52, 65, 269, 22, 'medium-fast'),
            (284, 'Masquerain', 12, 10, 70, 60, 62, 100, 82, 80, 454, None, 'medium-fast'),
            (285, 'Shroomish', 5, None, 60, 40, 60, 40, 60, 35, 295, 23, 'fluctuating'),
            (286, 'Breloom', 5, 7, 60, 130, 80, 60, 60, 70, 460, None, 'fluctuating'),
            (287, 'Slakoth', 1, None, 60, 60, 60, 35, 35, 30, 280, 18, 'slow'),
            (288, 'Vigoroth', 1, None, 80, 80, 80, 55, 55, 90, 440, 36, 'slow'),
            (289, 'Slaking', 1, None, 150, 160, 100, 95, 65, 100, 670, None, 'slow'),
            (290, 'Nincada', 12, 9, 31, 45, 90, 30, 30, 40, 266, 20, 'fluctuating'),
            (291, 'Ninjask', 12, 10, 61, 90, 45, 50, 50, 160, 456, None, 'fluctuating'),
            (292, 'Shedinja', 12, 14, 1, 90, 45, 30, 30, 40, 236, None, 'fluctuating'),
            (293, 'Whismur', 1, None, 64, 51, 23, 51, 23, 28, 240, 20, 'medium-slow'),
            (294, 'Loudred', 1, None, 84, 71, 43, 71, 43, 48, 360, 40, 'medium-slow'),
            (295, 'Exploud', 1, None, 104, 91, 63, 91, 73, 68, 490, None, 'medium-slow'),
            (296, 'Makuhita', 7, None, 72, 60, 30, 20, 30, 25, 237, 24, 'fluctuating'),
            (297, 'Hariyama', 7, None, 144, 120, 60, 40, 60, 50, 474, None, 'fluctuating'),
            (298, 'Azurill', 1, 18, 50, 20, 40, 20, 40, 20, 190, None, 'fast'),
            (299, 'Nosepass', 13, None, 30, 45, 135, 45, 90, 30, 375, None, 'medium-fast'),
            (300, 'Skitty', 1, None, 50, 45, 45, 35, 35, 50, 260, None, 'fast'),
            (301, 'Delcatty', 1, None, 70, 65, 65, 55, 55, 90, 400, None, 'fast'),
            (302, 'Sableye', 16, 14, 50, 75, 75, 65, 65, 50, 380, None, 'medium-slow'),
            (303, 'Mawile', 17, 18, 50, 85, 85, 55, 55, 50, 380, None, 'fast'),
            (304, 'Aron', 17, 13, 50, 70, 100, 40, 40, 30, 330, 32, 'slow'),
            (305, 'Lairon', 17, 13, 60, 90, 140, 50, 50, 40, 430, 42, 'slow'),
            (306, 'Aggron', 17, 13, 70, 110, 180, 60, 60, 50, 530, None, 'slow'),
            (307, 'Meditite', 7, 11, 30, 40, 55, 40, 55, 60, 280, 37, 'medium-fast'),
            (308, 'Medicham', 7, 11, 60, 60, 75, 60, 75, 80, 410, None, 'medium-fast'),
            (309, 'Electrike', 4, None, 40, 45, 40, 65, 40, 65, 295, 26, 'slow'),
            (310, 'Manectric', 4, None, 70, 75, 60, 105, 60, 105, 475, None, 'slow'),
            (311, 'Plusle', 4, None, 60, 50, 40, 85, 75, 95, 405, None, 'medium-fast'),
            (312, 'Minun', 4, None, 60, 40, 50, 75, 85, 95, 405, None, 'medium-fast'),
            (313, 'Volbeat', 12, None, 65, 73, 75, 47, 85, 85, 430, None, 'fluctuating'),
            (314, 'Illumise', 12, None, 65, 47, 75, 73, 85, 85, 430, None, 'fluctuating'),
            (315, 'Roselia', 5, 8, 50, 60, 45, 100, 80, 65, 400, None, 'medium-slow'),
            (316, 'Gulpin', 8, None, 70, 43, 53, 43, 53, 40, 302, 26, 'fluctuating'),
            (317, 'Swalot', 8, None, 100, 73, 83, 73, 83, 55, 467, None, 'fluctuating'),
            (318, 'Carvanha', 3, 16, 45, 90, 20, 65, 20, 65, 305, 30, 'slow'),
            (319, 'Sharpedo', 3, 16, 70, 120, 40, 95, 40, 95, 460, None, 'slow'),
            (320, 'Wailmer', 3, None, 130, 70, 35, 70, 35, 60, 400, 40, 'fluctuating'),
            (321, 'Wailord', 3, None, 170, 90, 45, 90, 45, 60, 500, None, 'fluctuating'),
            (322, 'Numel', 2, 9, 60, 60, 40, 65, 45, 35, 305, 33, 'medium-fast'),
            (323, 'Camerupt', 2, 9, 70, 100, 70, 105, 75, 40, 460, None, 'medium-fast'),
            (324, 'Torkoal', 2, None, 70, 85, 140, 85, 70, 20, 470, None, 'medium-fast'),
            (325, 'Spoink', 11, None, 60, 25, 35, 70, 80, 60, 330, 32, 'fast'),
            (326, 'Grumpig', 11, None, 80, 45, 65, 90, 110, 80, 470, None, 'fast'),
            (327, 'Spinda', 1, None, 60, 60, 60, 60, 60, 60, 360, None, 'fast'),
            (328, 'Trapinch', 9, None, 45, 100, 45, 45, 45, 10, 290, 35, 'medium-slow'),
            (329, 'Vibrava', 9, 15, 50, 70, 50, 50, 50, 70, 340, 45, 'medium-slow'),
            (330, 'Flygon', 9, 15, 80, 100, 80, 80, 80, 100, 520, None, 'medium-slow'),
            (331, 'Cacnea', 5, None, 50, 85, 40, 85, 40, 35, 335, 32, 'medium-slow'),
            (332, 'Cacturne', 5, 16, 70, 115, 60, 115, 60, 55, 475, None, 'medium-slow'),
            (333, 'Swablu', 1, 10, 45, 40, 60, 40, 75, 50, 310, 35, 'fluctuating'),
            (334, 'Altaria', 15, 10, 75, 70, 90, 70, 105, 80, 490, None, 'fluctuating'),
            (335, 'Zangoose', 1, None, 73, 115, 60, 60, 60, 90, 458, None, 'fluctuating'),
            (336, 'Seviper', 8, None, 73, 100, 60, 100, 60, 65, 458, None, 'fluctuating'),
            (337, 'Lunatone', 13, 11, 90, 55, 65, 95, 85, 70, 460, None, 'fast'),
            (338, 'Solrock', 13, 11, 90, 95, 85, 55, 65, 70, 460, None, 'fast'),
            (339, 'Barboach', 3, 9, 50, 48, 43, 46, 41, 60, 288, 30, 'medium-fast'),
            (340, 'Whiscash', 3, 9, 110, 78, 73, 76, 71, 60, 468, None, 'medium-fast'),
            (341, 'Corphish', 3, None, 43, 80, 65, 50, 35, 35, 308, 30, 'fluctuating'),
            (342, 'Crawdaunt', 3, 16, 63, 120, 85, 90, 55, 55, 468, None, 'fluctuating'),
            (343, 'Baltoy', 9, 11, 40, 40, 55, 40, 70, 55, 300, 36, 'medium-fast'),
            (344, 'Claydol', 9, 11, 60, 70, 105, 70, 120, 75, 500, None, 'medium-fast'),
            (345, 'Lileep', 13, 5, 66, 41, 77, 61, 87, 23, 355, 40, 'fluctuating'),
            (346, 'Cradily', 13, 5, 86, 81, 97, 81, 107, 43, 495, None, 'fluctuating'),
            (347, 'Anorith', 13, 12, 45, 95, 50, 40, 50, 75, 355, 40, 'fluctuating'),
            (348, 'Armaldo', 13, 12, 75, 125, 100, 70, 80, 45, 495, None, 'fluctuating'),
            (349, 'Feebas', 3, None, 20, 15, 20, 10, 55, 80, 200, None, 'fluctuating'),
            (350, 'Milotic', 3, None, 95, 60, 79, 100, 125, 81, 540, None, 'fluctuating'),
            (351, 'Castform', 1, None, 70, 70, 70, 70, 70, 70, 420, None, 'medium-fast'),
            (352, 'Kecleon', 1, None, 60, 90, 70, 60, 120, 40, 440, None, 'medium-slow'),
            (353, 'Shuppet', 14, None, 44, 75, 35, 63, 33, 45, 295, 37, 'fast'),
            (354, 'Banette', 14, None, 64, 115, 65, 83, 63, 65, 455, None, 'fast'),
            (355, 'Duskull', 14, None, 20, 40, 90, 30, 90, 25, 295, 37, 'fast'),
            (356, 'Dusclops', 14, None, 40, 70, 130, 60, 130, 25, 455, None, 'fast'),
            (357, 'Tropius', 5, 10, 99, 68, 83, 72, 87, 51, 460, None, 'slow'),
            (358, 'Chimecho', 11, None, 75, 50, 80, 95, 90, 65, 455, None, 'fast'),
            (359, 'Absol', 16, None, 65, 130, 60, 75, 60, 75, 465, None, 'medium-slow'),
            (360, 'Wynaut', 11, None, 95, 23, 48, 23, 48, 23, 260, 15, 'medium-fast'),
            (361, 'Snorunt', 6, None, 50, 50, 50, 50, 50, 50, 300, 42, 'medium-fast'),
            (362, 'Glalie', 6, None, 80, 80, 80, 80, 80, 80, 480, None, 'medium-fast'),
            (363, 'Spheal', 6, 3, 70, 40, 50, 55, 50, 25, 290, 32, 'medium-slow'),
            (364, 'Sealeo', 6, 3, 90, 60, 70, 75, 70, 45, 410, 44, 'medium-slow'),
            (365, 'Walrein', 6, 3, 110, 80, 90, 95, 90, 65, 530, None, 'medium-slow'),
            (366, 'Clamperl', 3, None, 35, 64, 85, 74, 55, 32, 345, None, 'fluctuating'),
            (367, 'Huntail', 3, None, 55, 104, 105, 94, 75, 52, 485, None, 'fluctuating'),
            (368, 'Gorebyss', 3, None, 55, 84, 105, 114, 75, 52, 485, None, 'fluctuating'),
            (369, 'Relicanth', 3, 13, 100, 90, 130, 45, 65, 55, 485, None, 'slow'),
            (370, 'Luvdisc', 3, None, 43, 30, 55, 40, 65, 97, 330, None, 'fast'),
            (371, 'Bagon', 15, None, 45, 75, 60, 40, 30, 50, 300, 30, 'slow'),
            (372, 'Shelgon', 15, None, 65, 95, 100, 60, 50, 50, 420, 50, 'slow'),
            (373, 'Salamence', 15, 10, 95, 135, 80, 110, 80, 100, 600, None, 'slow'),
            (374, 'Beldum', 17, 11, 40, 55, 80, 35, 60, 30, 300, 20, 'slow'),
            (375, 'Metang', 17, 11, 60, 75, 100, 55, 80, 50, 420, 45, 'slow'),
            (376, 'Metagross', 17, 11, 80, 135, 130, 95, 90, 70, 600, None, 'slow'),
            (377, 'Regirock', 13, None, 80, 100, 200, 50, 100, 50, 580, None, 'slow'),
            (378, 'Regice', 6, None, 80, 50, 100, 100, 200, 50, 580, None, 'slow'),
            (379, 'Registeel', 17, None, 80, 75, 150, 75, 150, 50, 580, None, 'slow'),
            (380, 'Latias', 15, 11, 80, 80, 90, 110, 130, 110, 600, None, 'slow'),
            (381, 'Latios', 15, 11, 80, 90, 80, 130, 110, 110, 600, None, 'slow'),
            (382, 'Kyogre', 3, None, 100, 100, 90, 150, 140, 90, 670, None, 'slow'),
            (383, 'Groudon', 9, None, 100, 150, 140, 100, 90, 90, 670, None, 'slow'),
            (384, 'Rayquaza', 15, 10, 105, 150, 90, 150, 90, 95, 680, None, 'slow'),
            (385, 'Jirachi', 17, 11, 100, 100, 100, 100, 100, 100, 600, None, 'slow'),
            (386, 'Deoxys', 11, None, 50, 150, 50, 150, 50, 150, 600, None, 'slow'),
            
            # Generation 4 (387-493)
            (387, 'Turtwig', 5, None, 55, 68, 64, 45, 55, 31, 318, 18, 'medium-slow'),
            (388, 'Grotle', 5, None, 75, 89, 85, 55, 65, 36, 405, 32, 'medium-slow'),
            (389, 'Torterra', 5, 9, 95, 109, 105, 75, 85, 56, 525, None, 'medium-slow'),
            (390, 'Chimchar', 2, None, 44, 58, 44, 58, 44, 61, 309, 14, 'medium-slow'),
            (391, 'Monferno', 2, 7, 64, 78, 52, 78, 52, 81, 405, 36, 'medium-slow'),
            (392, 'Infernape', 2, 7, 76, 104, 71, 104, 71, 108, 534, None, 'medium-slow'),
            (393, 'Piplup', 3, None, 53, 51, 53, 61, 56, 40, 314, 16, 'medium-slow'),
            (394, 'Prinplup', 3, None, 64, 66, 68, 81, 76, 50, 405, 36, 'medium-slow'),
            (395, 'Empoleon', 3, 17, 84, 86, 88, 111, 101, 60, 530, None, 'medium-slow'),
            (396, 'Starly', 1, 10, 40, 55, 30, 30, 30, 60, 245, 14, 'medium-slow'),
            (397, 'Staravia', 1, 10, 55, 75, 50, 40, 40, 80, 340, 34, 'medium-slow'),
            (398, 'Staraptor', 1, 10, 85, 120, 70, 50, 60, 100, 485, None, 'medium-slow'),
            (399, 'Bidoof', 1, None, 59, 45, 40, 35, 40, 31, 250, 15, 'medium-fast'),
            (400, 'Bibarel', 1, 3, 79, 85, 60, 55, 60, 71, 410, None, 'medium-fast'),
            (401, 'Kricketot', 12, None, 37, 25, 41, 25, 41, 25, 194, 10, 'medium-slow'),
            (402, 'Kricketune', 12, None, 77, 85, 51, 55, 51, 65, 384, None, 'medium-slow'),
            (403, 'Shinx', 4, None, 45, 65, 34, 40, 34, 45, 263, 15, 'medium-slow'),
            (404, 'Luxio', 4, None, 60, 85, 49, 60, 49, 60, 363, 30, 'medium-slow'),
            (405, 'Luxray', 4, None, 80, 120, 79, 95, 79, 70, 523, None, 'medium-slow'),
            (406, 'Budew', 5, 8, 40, 30, 35, 50, 70, 55, 280, None, 'medium-slow'),
            (407, 'Roserade', 5, 8, 60, 70, 65, 125, 105, 90, 515, None, 'medium-slow'),
            (408, 'Cranidos', 13, None, 67, 125, 40, 30, 30, 58, 350, 30, 'fluctuating'),
            (409, 'Rampardos', 13, None, 97, 165, 60, 65, 50, 58, 495, None, 'fluctuating'),
            (410, 'Shieldon', 13, 17, 30, 42, 118, 42, 88, 30, 350, 30, 'fluctuating'),
            (411, 'Bastiodon', 13, 17, 60, 52, 168, 47, 138, 30, 495, None, 'fluctuating'),
            (412, 'Burmy', 12, None, 40, 29, 45, 29, 45, 36, 224, 20, 'medium-fast'),
            (413, 'Wormadam', 12, 5, 60, 59, 85, 79, 105, 36, 424, None, 'medium-fast'),
            (414, 'Mothim', 12, 10, 70, 94, 50, 94, 50, 66, 424, None, 'medium-fast'),
            (415, 'Combee', 12, 10, 30, 30, 42, 30, 42, 70, 244, 21, 'medium-slow'),
            (416, 'Vespiquen', 12, 10, 70, 80, 102, 80, 102, 40, 474, None, 'medium-slow'),
            (417, 'Pachirisu', 4, None, 60, 45, 70, 45, 90, 95, 405, None, 'medium-fast'),
            (418, 'Buizel', 3, None, 55, 65, 35, 60, 30, 85, 330, 26, 'medium-fast'),
            (419, 'Floatzel', 3, None, 85, 105, 55, 85, 50, 115, 495, None, 'medium-fast'),
            (420, 'Cherubi', 5, None, 45, 35, 45, 62, 53, 35, 275, 25, 'medium-fast'),
            (421, 'Cherrim', 5, None, 70, 60, 70, 87, 78, 85, 450, None, 'medium-fast'),
            (422, 'Shellos', 3, None, 76, 48, 48, 57, 62, 34, 325, 30, 'medium-fast'),
            (423, 'Gastrodon', 3, 9, 111, 83, 68, 92, 82, 39, 475, None, 'medium-fast'),
            (424, 'Ambipom', 1, None, 75, 100, 66, 60, 66, 115, 482, None, 'fast'),
            (425, 'Drifloon', 14, 10, 90, 50, 34, 60, 44, 70, 348, 28, 'fluctuating'),
            (426, 'Drifblim', 14, 10, 150, 80, 44, 90, 54, 80, 498, None, 'fluctuating'),
            (427, 'Buneary', 1, None, 55, 66, 44, 44, 56, 85, 350, None, 'medium-fast'),
            (428, 'Lopunny', 1, None, 65, 76, 84, 54, 96, 105, 480, None, 'medium-fast'),
            (429, 'Mismagius', 14, None, 60, 60, 60, 105, 105, 105, 495, None, 'fast'),
            (430, 'Honchkrow', 16, 10, 100, 125, 52, 105, 52, 71, 505, None, 'medium-slow'),
            (431, 'Glameow', 1, None, 49, 55, 42, 42, 37, 85, 310, 38, 'fast'),
            (432, 'Purugly', 1, None, 71, 82, 64, 64, 59, 112, 452, None, 'fast'),
            (433, 'Chingling', 11, None, 45, 30, 50, 65, 50, 45, 285, None, 'fast'),
            (434, 'Stunky', 16, 8, 63, 63, 47, 41, 41, 74, 329, 34, 'medium-fast'),
            (435, 'Skuntank', 16, 8, 103, 93, 67, 71, 61, 84, 479, None, 'medium-fast'),
            (436, 'Bronzor', 17, 11, 57, 24, 86, 24, 86, 23, 300, 33, 'medium-fast'),
            (437, 'Bronzong', 17, 11, 67, 89, 116, 79, 116, 33, 500, None, 'medium-fast'),
            (438, 'Bonsly', 13, None, 50, 80, 95, 10, 45, 10, 290, None, 'medium-fast'),
            (439, 'Mime Jr.', 11, 18, 20, 25, 45, 70, 90, 60, 310, None, 'medium-fast'),
            (440, 'Happiny', 1, None, 100, 5, 5, 15, 65, 30, 220, None, 'fast'),
            (441, 'Chatot', 1, 10, 76, 65, 45, 92, 42, 91, 411, None, 'medium-slow'),
            (442, 'Spiritomb', 14, 16, 50, 92, 108, 92, 108, 35, 485, None, 'medium-fast'),
            (443, 'Gible', 15, 9, 58, 70, 45, 40, 45, 42, 300, 24, 'slow'),
            (444, 'Gabite', 15, 9, 68, 90, 65, 50, 55, 82, 410, 48, 'slow'),
            (445, 'Garchomp', 15, 9, 108, 130, 95, 80, 85, 102, 600, None, 'slow'),
            (446, 'Munchlax', 1, None, 135, 85, 40, 40, 85, 5, 390, None, 'slow'),
            (447, 'Riolu', 7, None, 40, 70, 40, 35, 40, 60, 285, None, 'medium-slow'),
            (448, 'Lucario', 7, 17, 70, 110, 70, 115, 70, 90, 525, None, 'medium-slow'),
            (449, 'Hippopotas', 9, None, 68, 72, 78, 38, 42, 32, 330, 34, 'slow'),
            (450, 'Hippowdon', 9, None, 108, 112, 118, 68, 72, 47, 525, None, 'slow'),
            (451, 'Skorupi', 8, 12, 40, 50, 90, 30, 55, 65, 330, 40, 'slow'),
            (452, 'Drapion', 8, 16, 70, 90, 110, 60, 75, 95, 500, None, 'slow'),
            (453, 'Croagunk', 8, 7, 48, 61, 40, 61, 40, 50, 300, 37, 'medium-fast'),
            (454, 'Toxicroak', 8, 7, 83, 106, 65, 86, 65, 85, 490, None, 'medium-fast'),
            (455, 'Carnivine', 5, None, 74, 100, 72, 90, 72, 46, 454, None, 'slow'),
            (456, 'Finneon', 3, None, 49, 49, 56, 49, 61, 66, 330, 31, 'fluctuating'),
            (457, 'Lumineon', 3, None, 69, 69, 76, 69, 86, 91, 460, None, 'fluctuating'),
            (458, 'Mantyke', 3, 10, 45, 20, 50, 60, 120, 50, 345, None, 'slow'),
            (459, 'Snover', 5, 6, 60, 62, 50, 62, 60, 40, 334, 40, 'slow'),
            (460, 'Abomasnow', 5, 6, 90, 92, 75, 92, 85, 60, 494, None, 'slow'),
            (461, 'Weavile', 16, 6, 70, 120, 65, 45, 85, 125, 510, None, 'medium-slow'),
            (462, 'Magnezone', 4, 17, 70, 70, 115, 130, 90, 60, 535, None, 'medium-fast'),
            (463, 'Lickilicky', 1, None, 110, 85, 95, 80, 95, 50, 515, None, 'medium-fast'),
            (464, 'Rhyperior', 9, 13, 115, 140, 130, 55, 55, 40, 535, None, 'slow'),
            (465, 'Tangrowth', 5, None, 100, 100, 125, 110, 50, 50, 535, None, 'medium-fast'),
            (466, 'Electivire', 4, None, 75, 123, 67, 95, 85, 95, 540, None, 'medium-fast'),
            (467, 'Magmortar', 2, None, 75, 95, 67, 125, 95, 83, 540, None, 'medium-fast'),
            (468, 'Togekiss', 18, 10, 85, 50, 95, 120, 115, 80, 545, None, 'fast'),
            (469, 'Yanmega', 12, 10, 86, 76, 86, 116, 56, 95, 515, None, 'medium-fast'),
            (470, 'Leafeon', 5, None, 65, 110, 130, 60, 65, 95, 525, None, 'medium-fast'),
            (471, 'Glaceon', 6, None, 65, 60, 110, 130, 95, 65, 525, None, 'medium-fast'),
            (472, 'Gliscor', 9, 10, 75, 95, 125, 45, 75, 95, 510, None, 'medium-slow'),
            (473, 'Mamoswine', 6, 9, 110, 130, 80, 70, 60, 80, 530, None, 'slow'),
            (474, 'Porygon-Z', 1, None, 85, 80, 70, 135, 75, 90, 535, None, 'medium-fast'),
            (475, 'Gallade', 11, 7, 68, 125, 65, 65, 115, 80, 518, None, 'slow'),
            (476, 'Probopass', 13, 17, 60, 55, 145, 75, 150, 40, 525, None, 'medium-fast'),
            (477, 'Dusknoir', 14, None, 45, 100, 135, 65, 135, 45, 525, None, 'fast'),
            (478, 'Froslass', 6, 14, 70, 80, 70, 80, 70, 110, 480, None, 'medium-fast'),
            (479, 'Rotom', 4, 14, 50, 50, 77, 95, 77, 91, 440, None, 'medium-fast'),
            (480, 'Uxie', 11, None, 75, 75, 130, 75, 130, 95, 580, None, 'slow'),
            (481, 'Mesprit', 11, None, 80, 105, 105, 105, 105, 80, 580, None, 'slow'),
            (482, 'Azelf', 11, None, 75, 125, 70, 125, 70, 115, 580, None, 'slow'),
            (483, 'Dialga', 17, 15, 100, 120, 120, 150, 100, 90, 680, None, 'slow'),
            (484, 'Palkia', 3, 15, 90, 120, 100, 150, 120, 100, 680, None, 'slow'),
            (485, 'Heatran', 2, 17, 91, 90, 106, 130, 106, 77, 600, None, 'slow'),
            (486, 'Regigigas', 1, None, 110, 160, 110, 80, 110, 100, 670, None, 'slow'),
            (487, 'Giratina', 14, 15, 150, 100, 120, 100, 120, 90, 680, None, 'slow'),
            (488, 'Cresselia', 11, None, 120, 70, 120, 75, 130, 85, 600, None, 'slow'),
            (489, 'Phione', 3, None, 80, 80, 80, 80, 80, 80, 480, None, 'slow'),
            (490, 'Manaphy', 3, None, 100, 100, 100, 100, 100, 100, 600, None, 'slow'),
            (491, 'Darkrai', 16, None, 70, 90, 90, 135, 90, 125, 600, None, 'slow'),
            (492, 'Shaymin', 5, None, 100, 100, 100, 100, 100, 100, 600, None, 'medium-slow'),
            (493, 'Arceus', 1, None, 120, 120, 120, 120, 120, 120, 720, None, 'slow')
        ]
        
        # Clear the table first to avoid duplicates
        cursor.execute("DELETE FROM pokemon")
        
        # Insert all Pokémon with their evolution levels and exp curves
        cursor.executemany('''
        INSERT INTO pokemon 
        (id, name, type1, type2, hp, attack, defense, special_attack, special_defense, speed, total_stats, evolution_level, exp_curve)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pokemon_data)
        
        print(f"Successfully inserted {len(pokemon_data)} Pokemon (Gen 1-4)")
    
    def _insert_gen5_6_pokemon(self, cursor):
        """Insert Gen 5-6 Pokemon (IDs 494-721) from exported file"""
        import sys
        import os
        # Get the project root directory (parent of src)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, project_root)
        from gen5_6_pokemon_export import GEN5_6_POKEMON
        
        # Convert data to exclude the 14th field (evolves_to_id) which doesn't exist in this table
        # Evolution data is stored in pokemon_evolutions table instead
        pokemon_data_converted = [
            (id, name, type1, type2, hp, attack, defense, sp_atk, sp_def, speed, total, evo_level, exp_curve)
            for id, name, type1, type2, hp, attack, defense, sp_atk, sp_def, speed, total, evo_level, exp_curve, _ in GEN5_6_POKEMON
        ]
        
        # Insert Gen 5-6 Pokemon
        cursor.executemany('''
        INSERT INTO pokemon 
        (id, name, type1, type2, hp, attack, defense, special_attack, special_defense, speed, total_stats, evolution_level, exp_curve)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pokemon_data_converted)
        
        print(f"Successfully inserted {len(GEN5_6_POKEMON)} Gen 5-6 Pokemon")
    
    def _insert_pokemon_learnsets(self, cursor):
        """Insert pokemon learnset data from exported file"""
        try:
            # Import the exported data
            import sys
            import os
            # Get the project root directory (parent of src)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, project_root)
            from pokemon_learnsets_export import POKEMON_LEARNSETS
            
            # Get valid pokemon IDs that exist in the database
            cursor.execute("SELECT id FROM pokemon")
            valid_pokemon_ids = set(row[0] for row in cursor.fetchall())
            
            # Filter learnsets to only include valid Pokemon
            filtered_learnsets = [
                entry for entry in POKEMON_LEARNSETS
                if entry[0] in valid_pokemon_ids  # entry[0] is pokemon_id
            ]
            
            skipped = len(POKEMON_LEARNSETS) - len(filtered_learnsets)
            
            cursor.executemany('''
                INSERT INTO pokemon_learnsets (pokemon_id, move_id, learn_method, learn_level, form)
                VALUES (?, ?, ?, ?, ?)
            ''', filtered_learnsets)
            print(f'✓ Inserted {len(filtered_learnsets)} pokemon learnset entries')
            if skipped > 0:
                print(f'  (Skipped {skipped} entries for Pokemon not in database)')
        except ImportError as e:
            print(f'⚠️  Warning: pokemon_learnsets_export.py not found in project root.')
            print('   Learnsets table will be empty.')
            print('   Run: py export_data.py to generate this file from existing database.')
        except Exception as e:
            print(f'✗ Error inserting learnsets: {e}')
            raise

    def _insert_pokemon_evolutions(self, cursor):
        """Insert pokemon evolution data from exported file"""
        try:
            # Import the exported data
            import sys
            import os
            # Get the project root directory (parent of src)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, project_root)
            from pokemon_evolutions_export import POKEMON_EVOLUTIONS
            
            # Get valid pokemon IDs that exist in the database
            cursor.execute("SELECT id FROM pokemon")
            valid_pokemon_ids = set(row[0] for row in cursor.fetchall())
            
            # Filter evolutions to only include valid Pokemon
            # Note: evolves_to_id can be None, which is OK
            filtered_evolutions = [
                entry for entry in POKEMON_EVOLUTIONS
                if entry[0] in valid_pokemon_ids and  # entry[0] is pokemon_id
                (entry[1] is None or entry[1] in valid_pokemon_ids)  # entry[1] is evolves_to_id
            ]
            
            skipped = len(POKEMON_EVOLUTIONS) - len(filtered_evolutions)
            
            cursor.executemany('''
                INSERT INTO pokemon_evolutions (pokemon_id, evolves_to_id, evolution_level)
                VALUES (?, ?, ?)
            ''', filtered_evolutions)
            print(f'✓ Inserted {len(filtered_evolutions)} pokemon evolution entries')
            if skipped > 0:
                print(f'  (Skipped {skipped} entries for Pokemon not in database)')
        except ImportError as e:
            print(f'⚠️  Warning: pokemon_evolutions_export.py not found in project root.')
            print('   Evolutions table will be empty.')
            print('   Run: py export_data.py to generate this file from existing database.')
        except Exception as e:
            print(f'✗ Error inserting evolutions: {e}')
            raise
    
    def _insert_abilities(self, cursor):
        """Insert abilities data from exported file"""
        try:
            # Import the exported data
            import sys
            import os
            # Get the project root directory (parent of src)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, project_root)
            from abilities_data_export import ABILITIES
            
            cursor.executemany('''
                INSERT INTO abilities (id, name, description, overworld_effect)
                VALUES (?, ?, ?, ?)
            ''', ABILITIES)
            print(f'✓ Inserted {len(ABILITIES)} abilities')
        except ImportError as e:
            print(f'⚠️  Warning: abilities_data_export.py not found in project root.')
            print('   Abilities table will be empty.')
        except Exception as e:
            print(f'✗ Error inserting abilities: {e}')
            raise

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
