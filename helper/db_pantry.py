"""
--------------------------------------------------------------------------------
Script Name:   db_pantry.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16

Description:
    This module handles all logic related to User Pantry management.
    It serves as the interface between the API/Frontend and the SQLite database.

    Key Features:
    - select_user_pantry: Retrieves inventory with joined ingredient names.
    - modify_pantry: A transactional function to Add/Remove items. 
      Handles 'Upsert' logic (Update if exists, Insert if new) and 
      automatic cleanup (Delete row if amount <= 0).

Dependencies:
    - sqlite3
    - pydantic_models.Item
    - item_helper
--------------------------------------------------------------------------------
"""


import sqlite3
from models.pydantic_models import Item, PantryAction
from helper.db_item import *
from helper.logger import logger, sql_logger

database = "cloudcookbook.db"

def select_user_pantry(uid:int) -> dict:
    """
    Searches for an User by ID.
    Returns a user pantry Dictionary
    """
    logger.debug(f"Starting select_user_pantry for UID: {uid}")
    # Validation: If no valid search criteria are given, stop immediately.
    if uid == -1:
        return None
    conn = None # Initialize for safety in finally block
    try:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row  # This allows us to access data by column name (e.g., row['name'])
        sql = """
        SELECT i.ingredient_name, p.amount 
        FROM pantry p
        JOIN items i ON p.ingredient_id = i.ingredient_id
        WHERE p.uid = ?
        """
        cursor = conn.cursor()
        sql_logger.info(f"Query: {sql} | Params: {(uid,)}")
        cursor.execute(sql, (uid,))
        rows = cursor.fetchall()
        if not rows:
            logger.debug(f"Pantry is empty for UID {uid}")
            return {}
        logger.debug(f"Retrieved {len(rows)} items for UID {uid}")
        return {row['ingredient_name']: row['amount'] for row in rows}
    except sqlite3.Error as e:
            logger.error(f"Database Error in select_user_pantry: {e}", exc_info=True)
            return None
    finally:
        if conn:
            conn.close()

def modify_pantry(uid: int, ingredient_name: str, amount: int, action: PantryAction)-> bool:
    """
    Unified logic to Add or Remove items from a user pantry.
    Assumes inputs are already validated and cleaned.
    
    Args:
        uid (int): The unique ID of the user owning the pantry.
        ingredient_name (str): The common name of the ingredient (e.g., "Potato").
        amount (int): The quantity to add or remove (must be > 0).
        action (PantryAction): The operation to perform (PantryAction.ADD or PantryAction.REMOVE).
    
    Returns:
        bool: True if the database operation was successful, False if validation failed or an error occurred.
    """
    logger.debug(f"Starting modify_pantry: User {uid} {action.value} {amount}x '{ingredient_name}'")
    conn = None
    # Basic Validation
    if uid == -1 or not ingredient_name or amount <= 0:
        logger.warning(f"Validation failed for pantry modification (UID: {uid}, Item: {ingredient_name})")
        return False
    try:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        with conn:
            cursor = conn.cursor()
            item_id = get_item_id(ingredient_name)
            
            # --- ADDITION LOGIC ---
            
            if action == PantryAction.ADD:
                if item_id == "N/A":
                    create_item(ingredient_name)
                    sql_check = "SELECT 1 FROM pantry WHERE uid=? AND ingredient_id=?"
                    item_id = get_item_id(ingredient_name)
                    sql_logger.info(f"Query: {sql_check} | Params: {(uid, item_id)}")
                cursor.execute(sql_check, (uid, item_id))
                
                exists = cursor.fetchone()
                if exists:
                    # Update: Add to existing
                    sql = "UPDATE pantry SET amount = amount + ? WHERE uid = ? AND ingredient_id = ?"
                    sql_logger.info(f"Query: {sql} | Params: {(uid, item_id)}")
                    cursor.execute(sql, (amount, uid, item_id))
                else:
                    # Insert: New Row
                    sql = "INSERT INTO pantry (amount, uid, ingredient_id) VALUES (?, ?, ?)"
                    sql_logger.info(f"Query: {sql} | Params: {(uid, item_id)}")
                    cursor.execute(sql, (amount, uid, item_id))
            # --- REMOVAL LOGIC ---
            elif action == PantryAction.REMOVE:
                if item_id == "N/A":
                    logger.warning(f"User {uid} tried to remove '{ingredient_name}', but it does not exist globally.")
                    return False # Can't remove an item that doesn't exist globally
                cursor.execute("SELECT * FROM pantry WHERE uid=? AND ingredient_id=?", (uid, item_id))
                exists = cursor.fetchone()
                if exists: # Update: Subtract amount
                    sql = "UPDATE pantry SET amount = amount - ? WHERE uid = ? AND ingredient_id = ?"
                    sql_logger.info(f"Query: {sql} | Params: {(uid, item_id)}")
                    cursor.execute(sql, (amount, uid, item_id))
                    # Cleanup: Check if empty (<= 0) and Delete if so
                    sql ="SELECT amount FROM pantry WHERE uid = ? AND ingredient_id = ?"
                    sql_logger.info(f"Query: {sql} | Params: {(uid, item_id)}")
                    cursor.execute(sql, (uid, item_id))
                    row = cursor.fetchone()
                    if row and row['amount'] <= 0:
                        sql ="DELETE FROM pantry WHERE uid = ? AND ingredient_id = ?"
                        sql_logger.info(f"Query: {sql} | Params: {(uid, item_id)}")
                        cursor.execute(sql, (uid, item_id))
                        logger.debug(f"Item {item_id} removed completely from User {uid}'s pantry.")
                else: # tried to remove item not in user's pantry
                    logger.warning(f"User {uid} tried to remove '{ingredient_name}' but does not have it.")
                    return False
            logger.info(f"Pantry Update Success: User {uid} {action.value}ed {amount} of '{ingredient_name}'")
            return True
    except Exception as e:
        logger.error(f"Database Error in modify_pantry: {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()
