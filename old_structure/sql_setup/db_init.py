"""
--------------------------------------------------------------------------------
Script Name:   db_init.py
Description:   Database Initialization / Seeder Script.
               
               This script prepares the 'cloudcookbook.db' for first-time use.
               1. Wipes existing data to ensure a clean state.
               2. Seeds the mandatory 'User' accounts (Admin, Team Members).
               3. Seeds the 'Global Ingredients' catalog (Top 100 Standard Items).
               
Usage:         Run once during deployment or setup:
               python db_init.py
--------------------------------------------------------------------------------
"""
import sqlite3
from helper.logger import logger, sql_logger

DB_FILE = "cloudcookbook.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ---------------------------------------------------------
# 1. INIT USERS
# ---------------------------------------------------------
def init_users():
    """Creates the 4 standard users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("--- Initializing Users ---")
    # SQLite handles IDs (1, 2, 3...) automatically via AUTOINCREMENT
    users = [
        ("ADMIN",), 
        ("Auren_1337",), 
        ("Memelord_Tommy",), 
        ("Nerd_Tubbe",)
    ]
# INSERT OR IGNORE avoids crashes if users already exist
    sql = "INSERT OR IGNORE INTO user (username) VALUES (?)"
    cursor.executemany(sql, users)
    sql_logger.info(f"Query: {sql} | Params: {(users,)}")
    conn.commit()
    conn.close()
    print("Users created.")
    logger.info("Users created.")

# ---------------------------------------------------------
# 2. INIT INGREDIENTS
# ---------------------------------------------------------
def init_ingredients():
    """Creates the Top 100 English Ingredients."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("--- Initializing Ingredients ---")

    item_list_names = [
        # Dairy & Eggs
        "butter", "eggs", "milk", "cheddar cheese", "parmesan cheese", 
        "mozzarella", "heavy cream", "yogurt", "sour cream", "cream cheese",
        # Veggies
        "onion", "garlic", "tomato", "potato", "carrot", 
        "bell pepper", "broccoli", "spinach", "cucumber", "lettuce",
        "mushroom", "zucchini", "ginger", "celery", "green onion",
        "corn", "avocado", "cauliflower", "sweet potato", "chili pepper",
        "peas", "green beans", "asparagus", "cabbage", "eggplant",
        "kale", "leek", "brussels sprouts", "beets", "radish",
        # Fruits
        "lemon", "lime", "apple", "banana", "orange", 
        "strawberry", "blueberry", "pineapple", "mango", "grapes",
        "peach", "pear", "watermelon", "cherry", "raspberry",
        # Meat
        "chicken breast", "ground beef", "bacon", "sausage", "salmon", 
        "tuna", "shrimp", "pork chop", "steak", "tofu",
        "ham", "turkey", "chicken thighs", "ground pork", "pepperoni",
        # Grains
        "rice", "spaghetti", "pasta", "flour", "bread", 
        "oats", "breadcrumbs", "tortilla", "noodles", "quinoa",
        # Condiments
        "olive oil", "vegetable oil", "soy sauce", "white vinegar", "balsamic vinegar",
        "sugar", "brown sugar", "honey", "mustard", "ketchup",
        "mayonnaise", "tomato paste", "tomato sauce", "chicken stock", "beef stock",
        "worcestershire sauce", "hot sauce", "maple syrup", "sesame oil", "bbq sauce",
        # Spices
        "basil", "oregano", "cumin", "paprika", "cinnamon",
        "thyme", "rosemary", "parsley", "coriander", "turmeric",
        "chili powder", "garlic powder", "onion powder", "nutmeg", "bay leaf",
        "cayenne pepper", "cloves", "vanilla extract", "cocoa powder", "chocolate chips",
        # Baking/Nuts
        "baking powder", "baking soda", "yeast", "cornstarch", "almonds", 
        "walnuts", "peanuts", "peanut butter", "cashews", "raisins"
    ]
    # Clean and Sort
    unique_items = sorted(list(set(item_list_names)))
    
    # Tuple format for executemany
    data_to_insert = [(name.lower(),) for name in unique_items]
    
    # Safer loop to avoid duplicates:
    count = 0
    for item in data_to_insert:
        # Check if exists
        sql = "INSERT INTO items (ingredient_name) VALUES (?)"
        sql2="SELECT 1 FROM items WHERE ingredient_name = ?"
        sql_logger.info(f"Query: {sql2} | Params: {(item,)}")
        cursor.execute(sql2, item)
        if not cursor.fetchone():
            cursor.execute(sql, item)
            sql_logger.info(f"Query: {sql} | Params: {(item,)}")

            count += 1

    conn.commit()
    conn.close()
    print(f"Ingredients initialized. Added {count} new items.")
    logger.info(f"Ingredients initialized. Added {count} new items.")


# ---------------------------------------------------------
# 3. INIT RECIPES (Real Recipes)
# ---------------------------------------------------------
def init_recipes():
    """Creates 4 real recipes with dynamic ID lookup."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("--- Initializing Recipes ---")

# Helper: Find Ingredient ID by Name
    def get_ing_id(name):
        sql = "SELECT ingredient_id FROM items WHERE ingredient_name = ?"
        cursor.execute(sql, (name.lower(),))
        sql_logger.info(f"Query: {sql} | Params: {(name.lower(),)}")

        result = cursor.fetchone()
        if result:
            return result[0]
        print(f"WARNING: Ingredient '{name}' not found in DB! Skipping.")
        logger.info(f"WARNING: Ingredient '{name}' not found in DB! Skipping.")
        return None
    
    real_recipes = [
        {
            "name": "Classic Pancakes",
            "desc": "Fluffy sunday breakfast pancakes. (Single Portion)",
            "creator": 2, # Auren
            "time": 20,
            "ingredients": {
                # Scaled to ~1 Person
                "flour": 60,   # Grams
                "milk": 100,   # ml
                "eggs": 1,     # count
                "butter": 1,   # "some" for frying
                "sugar": 1,    # "some"
                "baking powder": 1 # "pinch/spoon"
            },
            "steps": [
                "Mix flour, sugar and baking powder in a large bowl.",
                "Whisk milk and eggs in a separate jug.",
                "Combine wet and dry ingredients.",
                "Melt butter in pan and fry batter until golden."
            ]
        },
        {
            "name": "Spaghetti Aglio e Olio",
            "desc": "Simple, garlic-infused pasta. (Single Portion)",
            "creator": 3, # Tommy
            "time": 15,
            "ingredients": {
                # Scaled to 1 Person
                "spaghetti": 125,     # Grams (Standard serving)
                "garlic": 1,          # Clove
                "olive oil": 1,       # "drizzle/amount"
                "parsley": 1,         # "bunch/sprinkle"
                "parmesan cheese": 1  # "amount to taste"
            },
            "steps": [
                "Boil spaghetti in salted water until al dente.",
                "Slice garlic thinly and fry in olive oil gently.",
                "Toss pasta into the garlic oil.",
                "Add parsley and grated cheese before serving."
            ]
        },
        {
            "name": "Chicken Stir-Fry",
            "desc": "Healthy and quick weeknight dinner. (Single Portion)",
            "creator": 4, # Tubbe
            "time": 25,
            "ingredients": {
                # Scaled to 1 Person
                "chicken breast": 1,    # portion
                "rice": 1,              # portion
                "soy sauce": 1,        # "splash"
                "broccoli": 1,         # "portion"
                "onion": 1,            # "small onion"
                "ginger": 1            # "piece"
            },
            "steps": [
                "Cook rice according to package instructions.",
                "Cut chicken into strips and fry in a hot wok.",
                "Add chopped vegetables and stir-fry for 5 minutes.",
                "Add soy sauce and ginger, serve over rice."
            ]
        },
        {
            "name": "Caprese Salad",
            "desc": "Fresh Italian summer salad. (Single Portion)",
            "creator": 1, # Admin
            "time": 10,
            "ingredients": {
                # Scaled to 1 Person
                "tomato": 2,          # Count
                "mozzarella": 125,    # Grams (Standard ball size)
                "basil": 1,           # "handful"
                "olive oil": 1,       # "drizzle"
                "balsamic vinegar": 1 # "splash"
            },
            "steps": [
                "Slice tomatoes and mozzarella cheese.",
                "Arrange slices alternately on a plate.",
                "Sprinkle fresh basil leaves on top.",
                "Drizzle with olive oil and balsamic vinegar."
            ]
        }
    ]
    for recipe in real_recipes:
        # 1. Create Recipe Header
        # We DO NOT pass 'recipe_id' here. SQLite generates it (Auto Increment).
        sql = "INSERT INTO recipe (recipe_name, description, recipe_creator, time_needed) VALUES (?, ?, ?, ?)"
        cursor.execute(
            sql,
            (recipe["name"], recipe["desc"], recipe["creator"], recipe["time"])
        )
        sql_logger.info(f"Query: {sql} | Params: {(recipe["name"], recipe["desc"], recipe["creator"], recipe["time"])}")
        
        # Capture the ID that SQLite just generated for us
        new_recipe_id = cursor.lastrowid
        
        # 2. Add Steps (Linked to new_recipe_id)
        for idx, instruction in enumerate(recipe["steps"]):
            sql2 ="INSERT INTO recipe_steps (recipe_id, step_number, instruction) VALUES (?, ?, ?)"
            cursor.execute(
                sql2,
                (new_recipe_id, idx + 1, instruction)
            )
            sql_logger.info(f"Query: {sql2} | Params: {(new_recipe_id, idx + 1, instruction)}")
            
        # 3. Add Ingredients (Linked to new_recipe_id)
        for ing_name, amount in recipe["ingredients"].items():
            ing_id = get_ing_id(ing_name)
            if ing_id:
                sql = "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, needed) VALUES (?, ?, ?)"
                cursor.execute(
                    sql,
                    (new_recipe_id, ing_id, amount)
                )
                sql_logger.info(f"Query: {sql} | Params: {(new_recipe_id, ing_id, amount)}")

    conn.commit()
    conn.close()
    print(f"Recipes initialized. Created {len(real_recipes)} recipes.")
    logger.info(f"Recipes initialized. Created {len(real_recipes)} recipes.")
    
def seed_pantry_sql():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # User 1 is ADMIN
    uid = 1

    # We add MORE than strictly needed (e.g. 500g Flour instead of 60g)
    # so the admin has a stocked pantry.
    items_to_add = [
        # --- Ingredients for Classic Pancakes ---
        ("flour", 500),          # Need 60
        ("milk", 1000),          # Need 100
        ("eggs", 10),            # Need 1
        ("butter", 250),         # Need 1
        ("sugar", 500),          # Need 1
        ("baking powder", 50),   # Need 1

        # --- Ingredients for Spaghetti Aglio e Olio ---
        ("spaghetti", 500),      # Need 125
        ("garlic", 5),           # Need 1
        ("olive oil", 200),      # Need 1
        ("parsley", 20),         # Need 1
        ("parmesan cheese", 150) # Need 1
    ]

    print(f"--- Seeding Pantry for User {uid} (Direct SQL) ---")

    for name, amount in items_to_add:
        # SQL Logic:
        # 1. Find the ID for 'flour' inside the items table
        # 2. Insert that ID and the Amount into the pantry table
        # 3. If it already exists, REPLACE (overwrite) the old amount
        sql = """
        INSERT OR REPLACE INTO pantry (uid, ingredient_id, amount)
        VALUES (
            ?, 
            (SELECT ingredient_id FROM items WHERE ingredient_name = ?), 
            ?
        );
        """
        
        
        try:
            sql_logger.info(f"Query: {sql} | Params: {(uid, name, amount)}")

            cursor.execute(sql, (uid, name, amount))
            # Check if we actually changed a row (verifies ingredient name existed)
            if cursor.rowcount > 0:
                print(f"✅ Inserted: {amount}x {name}")
            else:
                print(f"⚠️  Warning: Could not find ingredient '{name}' in database.")
                
        except sqlite3.Error as e:
            print(f"❌ Database Error on {name}: {e}")

    conn.commit()
    conn.close()
    logger.info("--- Pantry Seeding Complete ---")


# ---------------------------------------------------------
# EXECUTION BLOCK
# ---------------------------------------------------------
def init_db():
    init_users()
    init_ingredients()
    init_recipes()
    seed_pantry_sql