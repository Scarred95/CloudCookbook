"""
--------------------------------------------------------------------------------
Script Name:   db_setup.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16

Description:
    Initializes the SQLite database schema.
    Creates tables for Users, Items, Recipes, Pantry, and their relationships.
    Run this script once to generate 'cloudcookbook.db'.

    This schema supports:
    - User Management
    - Global Ingredient Repository
    - Recipes with metadata (Description, Time, Creator)
    - Recipe Steps (1-to-N relation)
    - Recipe Ingredients (M-to-N relation)
    - User Pantry (M-to-N relation)

Dependencies:
    - sqlite3
--------------------------------------------------------------------------------
"""
import sqlite3

# Database file name
DB_FILE = "cloudcookbook.db"

def create_database():
    """
    Connects to SQLite and creates the necessary tables if they do not exist.
    """
    # Establish connection (creates the file if it does not exist)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # IMPORTANT: Enable Foreign Key support (defaults to OFF in SQLite)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create Tables (Order matters due to dependencies)
    
    # Table: User
    # 'active' stored as INTEGER (0 or 1)
    # 'member_since' as TEXT (Date as String)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        uid INTEGER PRIMARY KEY AUTOINCREMENT,
        active INTEGER DEFAULT 1,
        username TEXT NOT NULL UNIQUE,
        member_since TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: Items (Global Ingredients Registry)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ingredient_name TEXT NOT NULL
    );
    """)

    # Table: Recipe
    # Instructions removed here, moved to their own table 'recipe_steps'
    # recipe_creator is a Foreign Key pointing to user.uid
    # CHANGE: Added 'description' column
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe (
        recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_name TEXT NOT NULL,
        description TEXT,
        recipe_creator INTEGER,
        time_needed INTEGER,
        FOREIGN KEY(recipe_creator) REFERENCES user(uid)
    );
    """)

    # Table: recipe_steps - Instructions are now stored separately here
    # 'step_number' ensures the correct order (1., 2., 3. ...)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_steps (
        step_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        step_number INTEGER,
        instruction TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE
    );
    """)

    # Table: Pantry (User Inventory)
    # Composite Primary Key (uid + ingredient_id) ensures we don't create 
    # duplicate rows for the same item; we only update the 'amount'.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pantry (
        uid INTEGER,
        ingredient_id INTEGER,
        amount INTEGER,
        PRIMARY KEY (uid, ingredient_id),
        FOREIGN KEY (uid) REFERENCES user(uid) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES items(ingredient_id)
    );
    """)

    # Table: Recipe Ingredients (Ingredients required per Recipe)
    # Also here: Composite Primary Key consisting of recipe_id and ingredient_id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        recipe_id INTEGER,
        ingredient_id INTEGER,
        needed INTEGER,
        PRIMARY KEY (recipe_id, ingredient_id),
        FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES items(ingredient_id)
    );
    """)

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database schema successfully created.")