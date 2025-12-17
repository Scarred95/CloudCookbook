"""
--------------------------------------------------------------------------------
Script Name:   actionhelper.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16

Description:
    This module handles the Business Logic for 'Cooking' and 'Matchmaking'.
    It bridges the gap between raw database data and user actions.
--------------------------------------------------------------------------------
"""

import sqlite3
from models.pydantic_models import RecipeSummary
from helper.db_recipe import get_recipe_ingredients, get_recipe
from helper.db_pantry import select_user_pantry
from helper.logger import logger, sql_logger

DB_FILE = "cloudcookbook.db"

def get_cookable_recipes(uid: int) -> list[RecipeSummary]:
    """
    Matchmaking Logic:
    1. Loads the User's entire pantry into a Dictionary for O(1) lookups.
    2. Loads ALL Recipe requirements in a single optimized query.
    3. Compares them to find matches where User Amount >= Needed Amount.
    """
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get User Pantry
    sql = "SELECT ingredient_id, amount FROM pantry WHERE uid = ?"
    sql_logger.info(f"Query: {sql} | Params: {(uid,)}")

    cursor.execute("SELECT ingredient_id, amount FROM pantry WHERE uid = ?", (uid,))
    user_pantry = {row[0]: row[1] for row in cursor.fetchall()}
    if not user_pantry:
        logger.debug(f"User {uid} has an empty pantry. Returning 0 matches.")
        conn.close()
        return []
    
    # Get All Recipes & Their Ingredients
    sql = """
    SELECT r.recipe_id, r.recipe_name, r.description, r.time_needed, ri.ingredient_id, ri.needed, r.recipe_creator
    FROM recipe r
    JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
    """
    sql_logger.info(f"Query: {sql}")
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    
    # Organize Data
    recipes_map = {}
    for r_id, r_name, r_desc, r_time, ing_id, needed, r_creator in rows:
        if r_id not in recipes_map:
            recipes_map[r_id] = {
                "summary": RecipeSummary(
                    recipe_id=r_id, 
                    recipe_name=r_name, 
                    time_needed=r_time, 
                    recipe_creator=r_creator, 
                    description=r_desc
                ),
                "requirements": {}
            }
        recipes_map[r_id]["requirements"][ing_id] = needed
        
    # Comparison Logic
    cookable_recipes = []
    for r_id, data in recipes_map.items():
        requirements = data["requirements"]
        can_cook = True
        
        for ing_id, amount_needed in requirements.items():
            # Check 1: Do we have the ingredient ID?
            # Check 2: Do we have ENOUGH of it?
            user_amount = user_pantry.get(ing_id, 0)
            
            if user_amount < amount_needed:
                can_cook = False
                break # Optimization: Stop checking this recipe immediately if one item fails
        
        if can_cook:
            cookable_recipes.append(data["summary"])
            
        logger.info(f"Matchmaking for User {uid}: Found {len(cookable_recipes)} cookable recipes.")
    return cookable_recipes
    
def cook_recipe(uid: int, recipe_id: int) -> dict:
    """
    Transactional Cooking Action:
    1. Validates ingredient availability
    2. Opens a Database Transaction.
    3. Deducts ingredients one by one.
    4. Commits on success or Rolls Back on error.
    """
    # --- Pre-Flight Validation ---
    requirements = get_recipe_ingredients(recipe_id)
    user_pantry = select_user_pantry(uid)
    recipe_info = get_recipe(recipe_id)
    if not recipe_info:
        return {"status": "error", "message": "Recipe not found."}

    # Validation Loop
    missing_items = []
    for ingredient_name, needed_amount in requirements.items():
        user_has = user_pantry.get(ingredient_name, 0)
        
        if user_has < needed_amount:
            missing_items.append(f"{ingredient_name} (Need {needed_amount}, Have {user_has})")

    if missing_items:
        logger.warning(f"User {uid} failed to cook {recipe_id}. Missing: {missing_items}")
        return {
            "status": "failed", 
            "message": "Not enough ingredients!", 
            "missing": missing_items
        }
        
    # Execution of removal
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        logger.info(f"User {uid} cooking '{recipe_info.recipe_name}'...")
        # Iterate and Subtract
        for ingredient_name, needed_amount in requirements.items():
            # Subtraction Query
            sql = """
            UPDATE pantry 
            SET amount = amount - ? 
            WHERE uid = ? 
            AND ingredient_id = (SELECT ingredient_id FROM items WHERE ingredient_name = ?)
            """
            sql_logger.info(f"Query: {sql} | Params: {(needed_amount, uid, ingredient_name)}")
            cursor.execute(sql, (needed_amount, uid, ingredient_name))
            
        conn.commit()
        logger.info(f"Cooking complete. Pantry updated for User {uid}.")
        
        return {
            "status": "success", 
            "message": f"Successfully cooked {recipe_info.recipe_name}! Ingredients removed from pantry."
        }
    except Exception as e:
        conn.rollback() # Undo changes if something crashes halfway!
        logger.error(f"Cooking Transaction Failed: {e}")
        return {"status": "error", "message": "Database error during cooking."}
        
    finally:
        conn.close()