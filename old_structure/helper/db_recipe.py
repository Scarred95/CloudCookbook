"""
--------------------------------------------------------------------------------
Script Name:   db_recipe.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16

Description:
    This module handles the database logic for managing Recipes.
    It manages the interactions with the 'recipe' table and its associated 
    child tables ('recipe_steps', 'recipe_ingredients').
    
    It serves as the data layer that converts raw SQLite rows into validated 
    Pydantic 'Recipe' objects and handles complex transactional updates.

Key Features:
    - create_recipe: Atomic transaction that inserts a recipe, steps, and 
      links ingredients (including auto-creation of new items).
    - update_recipe: "Wipe and Rewrite" strategy to handle full recipe updates 
      safely, preventing ghost data in steps or ingredients.
    - get_recipe: Fetches a full detailed recipe object.
    - get_all_recipes: Fetches list of recipes (currently full detail).

Dependencies:
    - sqlite3
    - pydantic_models (Recipe class)
    - item_helper (for Pre-Flight item existence checks)
--------------------------------------------------------------------------------
"""
import sqlite3
from models.pydantic_models import Recipe, Item, User, RecipeSummary
from helper.db_item import get_item_id, create_item
from helper.logger import logger, sql_logger

database = "cloudcookbook.db"

def create_recipe(recipe: Recipe) -> int | bool:
    """
    Inserts a new recipe, its steps, and ingredients in ONE atomic transaction.
    Fixes 'Database Locked' errors by keeping everything inside one connection.
    """
    logger.debug(f"Starting creation process for recipe: '{recipe.recipe_name}'")
    
    # Pre Check: Ensure all ingredients exist globally
    # Before opening a transaction, we ensure every ingredient name has an ID.
    name_to_id_map = {}
    for name in recipe.recipe_ingredients.keys():
        ing_id = get_item_id(name)
        if ing_id == "N/A":
            logger.debug(f"Ingredient '{name}' missing. Creating it now...")
            create_item(name)
            ing_id = get_item_id(name)
        
        name_to_id_map[name] = ing_id

    conn = None # Initialize for safety
    creator_id = recipe.recipe_creator if recipe.recipe_creator is not None else 1
    
    # Prepare SQL Statements
    sql_recipe = "INSERT INTO recipe (recipe_name, description, recipe_creator, time_needed) VALUES (?,?,?,?)"
    sql_ing_link = "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, needed) VALUES (?,?,?)"
    sql_step = "INSERT INTO recipe_steps (recipe_id, step_number, instruction) VALUES (?,?,?)"
    
    try:
        conn = sqlite3.connect(database)
        
        # Transaction Start
        # 'with conn' ensures atomic commit/rollback for all 3 tables
        with conn: 
            cursor = conn.cursor()
            
            # Insert Main Recipe Data
            params_main = (recipe.recipe_name, recipe.description, creator_id, recipe.time_needed)
            sql_logger.info(f"Query: {sql_recipe} | Params: {params_main}")
            cursor.execute(sql_recipe, params_main)
            
            # Retrieve the auto-generated Recipe ID to link children
            new_recipe_id = cursor.lastrowid
            
            # Insert Ingredients (Mapping Table)
            for name, amount in recipe.recipe_ingredients.items():
                ing_id = name_to_id_map[name]
                
                params_ing = (new_recipe_id, ing_id, amount)
                sql_logger.info(f"Query: {sql_ing_link} | Params: {params_ing}")
                cursor.execute(sql_ing_link, params_ing)
            
            # Insert Steps
            for index, instruction in enumerate(recipe.instructions):
                # index + 1 ensures steps start at 1, not 0
                params_step = (new_recipe_id, index + 1, instruction)
                sql_logger.info(f"Query: {sql_step} | Params: {params_step}")
                cursor.execute(sql_step, params_step)
                
            logger.info(f"Successfully created Recipe '{recipe.recipe_name}' (ID: {new_recipe_id})")
            return new_recipe_id

    except Exception as e:
        logger.error(f"Failed to create recipe '{recipe.recipe_name}': {e}", exc_info=True)
        return False
    finally:
        # Cleanup
        if conn: conn.close()

def get_recipe_ingredients(recipe_id: int) -> dict[str, int]:
    """
    Fetches ingredients for a specific recipe.
    Uses a JOIN to replace IDs with readable Names.
    
    Returns:
        dict: { "Ingredient Name": Amount } (e.g., {"Mehl": 500, "Milch": 200})
    """
    logger.debug(f"Fetching ingredients for Recipe ID: {recipe_id}")
    conn = None # Initialize for safety
    try:
        conn = sqlite3.connect(database)
        
        # Complex Query: Join 'recipe_ingredients' with 'items' table
        sql = """
        SELECT i.ingredient_name, ri.needed 
        FROM recipe_ingredients ri
        JOIN items i ON ri.ingredient_id = i.ingredient_id
        WHERE ri.recipe_id = ?
        """
        
        with conn:
            sql_logger.info(f"Query: {sql} | Params: {(recipe_id,)}")
            conn.row_factory = sqlite3.Row # Allows access by column name
            cursor = conn.cursor()
            cursor.execute(sql, (recipe_id,))
            rows = cursor.fetchall()
            
            # Handle Empty Results
            if not rows:
                logger.debug(f"No ingredients found for Recipe ID {recipe_id}")
                return {}
            
            # Data Transformation
            # Takes the "ingredient_name" column as Key and "needed" column as Value
            logger.debug(f"Retrieved {len(rows)} ingredients for Recipe ID {recipe_id}")
            return {row["ingredient_name"]: row["needed"] for row in rows}
            
    except sqlite3.Error as e:
        logger.error(f"Error reading ingredients for recipe {recipe_id}: {e}", exc_info=True)
        return {} # Return empty dict on error for safety
    finally:
        if conn:
            conn.close()

def get_recipe_steps(recipe_id:int) -> list | None:
    """
    Fetches all instructions for a specific recipe.
    Returns a list of strings (e.g., ['Chop onions', 'Boil water']).
    """
    logger.debug(f"Fetching steps for Recipe ID: {recipe_id}")
    conn = None # Initialize for safety in finally block
    try:
        conn = sqlite3.connect(database)
        # Query: Order by step_number to ensure the recipe makes sense!
        sql = "SELECT instruction FROM recipe_steps WHERE recipe_id = ? ORDER BY step_number ASC"
        with conn:
            conn.row_factory = sqlite3.Row # Allows access by column name
            cursor = conn.cursor()
            sql_logger.info(f"Query: {sql} | Params: {(recipe_id,)}")
            cursor.execute(sql, (recipe_id,))
            rows = cursor.fetchall()
            
            # Handle Empty Results
            # If no steps found, return empty list (not None)
            if not rows:
                logger.debug(f"No steps found for Recipe ID {recipe_id}")
                return []
            
            # Data Transformation
            # List Comprehension: Extract the text string from every row object
            logger.debug(f"Retrieved {len(rows)} steps for Recipe ID {recipe_id}")
            return [row["instruction"] for row in rows] #Extract just the string from each row, puts them into a List
            
    except sqlite3.Error as e:
            logger.error(f"Error reading steps for recipe {recipe_id}: {e}", exc_info=True)
            return [] # Return empty list on error for safety
    finally:
        if conn:
            conn.close()

def get_recipe(recipe_id: int) -> Recipe | None:
    """
    Fetches a full Recipe object, including its list of instructions.
    """
    logger.debug(f"Starting full fetch for Recipe ID: {recipe_id}")
    conn = None # Initialize for safety in finally block
    gotten_recipe: Recipe =()
    
    # Fetch Basic Data
    sql_select = """
        SELECT recipe_id, recipe_name, description, recipe_creator, time_needed
        FROM recipe WHERE recipe_id = ?
        """

    try:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql_logger.info(f"Query: {sql_select} | Params: {(recipe_id,)}")
        cursor.execute(sql_select, (recipe_id,))
        row = cursor.fetchone()
        
        if row is None:
            logger.debug(f"Recipe ID {recipe_id} not found.")
            return None
            
        # Conversion: Convert Row to Dict for mutability
        # Convert to dict INSIDE the try block
        row_dict = dict(row)
    except sqlite3.Error as e:
            print(f"Error retrieving recipe {recipe_id}: {e}")
            return None 
    finally:
        if conn:
            conn.close()
            
    # Fetch Children Data (Instructions & Ingredients)
    # Populate the missing 'instructions' field using helper functions
    row_dict['instructions'] = get_recipe_steps(recipe_id)
    row_dict['recipe_ingredients'] = get_recipe_ingredients(recipe_id)
    
    # Model Creation & Validation
    try:
        recipe_obj = Recipe(**row_dict)
        return recipe_obj
    except Exception as e: # Catch ValidationErrors from Pydantic
        logger.error(f"Data Validation Error for Recipe {recipe_id}: {e}", exc_info=True)
        return None
    
def update_recipe(recipe_id: int, updated_recipe: Recipe) -> Recipe | None:
    """
    Updates an existing recipe in the 'recipe' table 
    and overwrites the steps in the 'recipe_steps' table.
    """
    logger.debug(f"Starting update process for Recipe ID: {recipe_id}")
    
    conn = None # Initialize for safety in finally block
    
    # Define SQL statements
    sql_check = "SELECT recipe_id FROM recipe WHERE recipe_id = ?"
    
    sql_update_main = """
    UPDATE recipe 
    SET recipe_name = ?, description = ?, recipe_creator = ?, time_needed = ? 
    WHERE recipe_id = ?
    """
    # Delete strategies for child tables (Wipe & Rewrite)
    sql_delete_steps = "DELETE FROM recipe_steps WHERE recipe_id = ?"
    
    sql_insert_step = """
    INSERT INTO recipe_steps (recipe_id, step_number, instruction) 
    VALUES (?,?,?)
    """
    
    sql_del_ings = "DELETE FROM recipe_ingredients WHERE recipe_id = ?"
    sql_ins_ing = """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, needed)
    VALUES (?,?,?)"""
    
    # Pre Check: Ensure all new ingredients exist
    name_to_id_map_updated = {}
    for name in updated_recipe.recipe_ingredients.keys():
        ing_id = get_item_id(name)
        if ing_id == "N/A":
            logger.debug(f"New ingredient detected in update: '{name}'. Creating...")
            create_item(name)
            ing_id = get_item_id(name)
        name_to_id_map_updated[name] = ing_id
    
    # Fallback logic similar to create_recipe
    if updated_recipe.recipe_creator is None:
        updated_recipe.recipe_creator = 1

    try:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check Existence
        sql_logger.info(f"Query: {sql_check} | Params: {(recipe_id,)}")
        cursor.execute(sql_check, (recipe_id,))
        if cursor.fetchone() is None:
            logger.warning(f"Update failed: Recipe ID {recipe_id} not found.")
            return None

        # Update Base Data (Recipe Table)
        params_main = (updated_recipe.recipe_name, updated_recipe.description, updated_recipe.recipe_creator, updated_recipe.time_needed, recipe_id)
        sql_logger.info(f"Query: {sql_update_main} | Params: {params_main}")
        cursor.execute(sql_update_main, params_main)

        # Update Steps (Delete Old -> Insert New)
        # Delete old steps
        sql_logger.info(f"Query: {sql_delete_steps} | Params: {(recipe_id,)}")
        cursor.execute(sql_delete_steps, (recipe_id,))

        # Insert new steps
        # We build a list of tuples for executemany, which is efficient and clean
        if updated_recipe.instructions:
            steps_data = []
            n = 1 # Counter for step_number
            for instruction in updated_recipe.instructions:
                steps_data.append((recipe_id, n, instruction))
                n += 1
            sql_logger.info(f"Query: {sql_insert_step} | Batch Size: {len(steps_data)}")
            cursor.executemany(sql_insert_step, steps_data)
            
        # Update Ingredients (Delete Old -> Insert New)
        sql_logger.info(f"Query: {sql_del_ings} | Params: {(recipe_id,)}")
        cursor.execute(sql_del_ings, (recipe_id,))
        
        if updated_recipe.recipe_ingredients:
                # Build list for executemany [(id, ing_id, amount)...]
                ing_data = []
                for name, amount in updated_recipe.recipe_ingredients.items():
                    ing_id = name_to_id_map_updated[name]
                    ing_data.append((recipe_id, ing_id, amount))
                sql_logger.info(f"Query: {sql_ins_ing} | Batch Size: {len(ing_data)}")
                cursor.executemany(sql_ins_ing, ing_data)
            
        # Finalize Transaction
        conn.commit()
        
        # Set ID and return the updated object
        updated_recipe.recipe_id = recipe_id
        logger.info(f"Successfully updated Recipe {recipe_id} ('{updated_recipe.recipe_name}')")
        return updated_recipe

    except sqlite3.Error as e:
        logger.error(f"Error updating recipe {recipe_id}: {e}", exc_info=True)
        if conn:
            conn.rollback() # Rollback changes on error
        return None
    finally:
        if conn:
            conn.close()

def get_all_recipes_summary():
    """
    Fetches the metadata for all recipes.
    Highly optimized: 1 Database Query, 0 Loops.
    """
    logger.debug("Starting get_all_recipes_summary")
    conn = None 
    recipes_list = []
    
    # Query: Select only needed columns for performance
    # We only grab what we need for the card/list view
    sql = "SELECT recipe_id, recipe_name, description, recipe_creator, time_needed FROM recipe"

    try:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        sql_logger.info(f"Query: {sql} | Params: None")
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # Iteration & Mapping
        for row in rows:
            try:
                # Direct mapping from Dict to Pydantic Model
                summary = RecipeSummary(**dict(row))
                recipes_list.append(summary)
            except Exception as e:
                logger.warning(f"Skipping invalid recipe row: {e}")
                continue
        logger.debug(f"Retrieved {len(recipes_list)} recipe summaries")
        return recipes_list

    except sqlite3.Error as e:
        logger.error(f"Error retrieving recipes: {e}", exc_info=True)
        return []
    finally:
        if conn: conn.close()