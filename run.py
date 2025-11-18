#!/usr/bin/env python3
"""
Pokemon Battle Move Database Launcher
"""

from src.main import main
from src.add_pokemon_data import main as init_pokemon

if __name__ == "__main__":
    main()
    init_pokemon()