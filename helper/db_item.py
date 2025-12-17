"""
--------------------------------------------------------------------------------
Script Name:   db_item.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16

Description:
    This module handles the 'Global Ingredient' database logic (the 'items' table).
    It allows the application to resolve Names to IDs and strictly controls
    duplicate item creation.

    Key Features:
    - get_item_name: Resolves ID -> String (Safe Read)
    - get_item_id: Resolves String -> ID (Safe Read)
    - create_item: Creates new global ingredients (Atomic Write with Duplicate Check)

Dependencies:
    - sqlite3
--------------------------------------------------------------------------------
"""



import sqlite3
from helper.logger import logger, sql_logger
database = "cloudcookbook.db"

def get_item_name(item_id: int) -> str | None:
    """
    Searches for an ingredient_name by ID.
    Returns the name of the item as a String, or "N/A" if not found.
    """
    # Validation
    logger.debug(f"Starting lookup for item_id: {item_id}")
    if item_id is None or item_id < 0:
        return "N/A"
        
    conn = None # Initialize for safety in finally block
    sql = "SELECT ingredient_name FROM items WHERE ingredient_id = ?"
    
    try:
        conn = sqlite3.connect(database)
        # Database Setup: Use Row Factory
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        sql_logger.info(f"Query: {sql} | Params: {(item_id,)}")
        
        # Execution
        cursor.execute(sql, (item_id,))
        result = cursor.fetchone()
        
        # Result Handling
        if result:
            logger.debug(f"Found item: '{str(result['ingredient_name'])}' (ID: {item_id})")
            return str(result["ingredient_name"])
        else:
            logger.debug(f"Item ID {item_id} not found in DB.")
            return "N/A"
            
    except sqlite3.Error as e:
        logger.error(f"Database Error in get_item_name for ID {item_id}: {e}", exc_info=True)
        return None
    finally:
        # Cleanup
        if conn:
            conn.close()

def get_item_id(item_name: str) -> int | str | None:
    """
    Searches for an ingredient_id by name.
    Returns the ID as an Integer if found, otherwise "N/A".
    """
    logger.debug(f"Starting get_item_id for Name: {item_name}")
    
    # Validation
    if not item_name:
        return "N/A"
        
    conn = None # Initialize for safety in finally block
    sql = "SELECT ingredient_id FROM items WHERE ingredient_name = ?"
    
    try:
        conn = sqlite3.connect(database)
        # Database Setup
        conn.row_factory = sqlite3.Row 
        
        cursor = conn.cursor()
        sql_logger.info(f"Query: {sql} | Params: {(item_name,)}")

        # Execution
        cursor.execute(sql, (item_name,))
        result = cursor.fetchone()
        
        # Result Handling
        if result:
            # Return just the number
            logger.debug(f"Found ID {int(result['ingredient_id'])} for name '{item_name}'")
            return int(result['ingredient_id'])
        else:
            logger.debug(f"No ID found for name '{item_name}'")
            return "N/A"

    except sqlite3.Error as e:
        logger.error(f"Database Error in get_item_id: {e}", exc_info=True)
        return None
        
    finally:
        # Cleanup
        if conn:
            conn.close()

def create_item(ingredient_name: str) -> bool:
    """
    Inserts a new ingredient into the database by name.
    Checks for duplicates first.
    
    Args:
        ingredient_name (str): Name of the item to create.
        
    Returns:
        bool: True if created successfully, False if it already exists or input is invalid.
    """
    logger.debug(f"Starting create_item for Name: {ingredient_name}")

    # Validation
    if not ingredient_name:
        logger.warning("Attempted to create item with empty name.")
        return False
        
    # Duplicate Check (Pre-Flight)
    existing_id = get_item_id(ingredient_name)
    if existing_id != "N/A": # if get_item_id returns a number, it exists.
        logger.debug(f"Skipping creation: '{ingredient_name}' already exists (ID: {existing_id})")
        return False 

    conn = None # Initialize for safety in finally block
    sql_insert = "INSERT INTO items (ingredient_name) VALUES (?)"

    try: 
        conn = sqlite3.connect(database)
        # Transaction Block
        with conn:
            cursor = conn.cursor()
            sql_logger.info(f"Query: {sql_insert} | Params: {(ingredient_name,)}")
            cursor.execute(sql_insert, (ingredient_name,))
            
            # Confirmation
            new_id = cursor.lastrowid
            logger.info(f"Successfully created Item '{ingredient_name}' (ID: {new_id})")
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Failed to create item '{ingredient_name}': {e}", exc_info=True)
        return False 
    finally:
        # Cleanup
        if conn:
            conn.close()