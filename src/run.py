#!/usr/bin/env python3
"""
Pokemon Battle Simulator Launcher
Manages database initialization and starts the main application
"""
import sys
import os

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from add_pokemon_data import PokemonDataManager
import main as main_app

def setup_database():
    """Initialize database with all required data"""
    print("=" * 60)
    print("Pokemon Battle Simulator - Database Setup")
    print("=" * 60)
    
    # Check if database exists
    db_path = "data/pokemon_battle.db"
    db_exists = os.path.exists(db_path)
    
    if db_exists:
        response = input("\nDatabase already exists. Reinitialize? (y/N): ").strip().lower()
        if response != 'y':
            print("Using existing database")
            return
        print("\nReinitializing database...")
        os.remove(db_path)
    
    # Initialize database
    print("\nCreating database structure...")
    db = DatabaseManager()
    db.initialize_database()
    print("Database structure created")
    
    # Add Pokemon data
    print("\nAdding Pokemon data...")
    pokemon_db = PokemonDataManager()
    pokemon_db.initialize_pokemon_data()
    
    print("\n" + "=" * 60)
    print("Database setup complete!")
    print("=" * 60)

def run_application():
    """Start the main application"""
    print("\nStarting Pokemon Battle Simulator...\n")
    main_app.main()

if __name__ == "__main__":
    try:
        setup_database()
        run_application()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)