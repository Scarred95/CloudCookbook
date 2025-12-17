"""
--------------------------------------------------------------------------------
Script Name:   main.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16

Description:
    This module constitutes the API Layer (Entry Point) of the CloudCookbook application.
    It initializes the FastAPI instance and defines the HTTP endpoints (Routes)
    that act as the interface between the Frontend/User and the backend logic.

    It handles request validation using Pydantic models and delegates database
    operations to the respective helper modules (Separation of Concerns).
--------------------------------------------------------------------------------
"""
from contextlib import asynccontextmanager
import time
import os
from fastapi import FastAPI, HTTPException, Request
from sql_setup.db_init import init_db
from sql_setup.db_setup import create_database
from models.pydantic_models import User, Recipe, RecipeSummary, ItemCreateRequest, PantryModifyRequest, PantryAction
from helper.db_recipe import create_recipe, get_recipe, get_all_recipes_summary, update_recipe, get_recipe_ingredients
from helper.db_item import get_item_name, get_item_id, create_item
from helper.db_pantry import select_user_pantry, modify_pantry
from helper.db_user import create_user, get_user_by_id, get_user_by_name, update_user
from helper.logger import api_logger, logger
from helper.actionhelper import get_cookable_recipes, cook_recipe

# Database file name
DB_FILE = "cloudcookbook.db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    if not os.path.exists(DB_FILE):
        logger.warning(f"Database '{DB_FILE}' not found. Creating and Seeding...")
        try:
            create_database()
            logger.info("--- Database creation Complete ---")
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
        try:
            init_db()
            logger.info("--- Database Initialization Complete ---")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    else:
        logger.info(f"Database '{DB_FILE}' found. Skipping initialization.")
    yield
    logger.info("Server shutting down...")


# Define API Metadata
tags_metadata = [
    {
        "name": "Users",
        "description": "User management (Login, Create, Update).",
    },
    {
        "name": "Pantry",
        "description": "Inventory management (Add/Remove ingredients).",
    },
    {
        "name": "Recipes",
        "description": "Search, create, and manage recipes.",
    },
    {
        "name": "Items",
        "description": "Global ingredient database operations.",
    },
    {
        "name": "Matchmaking",
        "description": "Find what you can cook right now.",
    }
 ]

# Define the API APP
app = FastAPI(
    title="CloudCookBook API",
    description="API for the CloudCookBook",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# --- MIDDLEWARE (Logging) ---
@app.middleware("http")
async def log_api_calls(request: Request, call_next):
    """
    Middleware that intercepts every request to log traffic data.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Log: METHOD path - Status - IP - Duration
    log_message = f"{request.method} {request.url.path} - {response.status_code} - {request.client.host} - {process_time:.2f}ms"
    api_logger.info(log_message)
    
    return response

# ITEM ENDPOINTS 

@app.get("/items/{item_id}", response_model=str, tags=["Items"])
def read_item_name(item_id: int):
    """Gets the ingredient name by the provided item_id."""
    name = get_item_name(item_id)
    if name == "N/A" or None:
        raise HTTPException(status_code=404, detail="Item not found.")
    return str(name)

@app.get("/items/search/{name}", response_model=int, tags=["Items"])
def read_item_id(name: str):
    """Gets item_id by the provided ingredient name"""
    item_id = get_item_id(name)
    if item_id == "N/A":
        raise HTTPException(status_code=404, detail="Item not found.")
    return item_id

@app.post("/items", status_code=201, tags=["Items"])
def create_new_item(item_data: ItemCreateRequest):
    """Creates new item in database"""
    success = create_item(item_data.ingredient_name)
    if not success:
        raise HTTPException(status_code=400, details="Items already exists or invalid input.")
    return {"message": f"Item '{item_data.ingredient_name}' created successfully."}

# PANTRY ENDPOINTS

@app.get("/pantry/{uid}", tags=["Pantry"])
def get_pantry(uid:int):
    """Gets data from user's panrty"""
    pantry = select_user_pantry(uid)
    if pantry is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return pantry

@app.post("/pantry/{uid}",status_code=201, tags=["Pantry"])
def update_pantry(uid: int, request: PantryModifyRequest):
    """Updates data in the user's pantry."""
    success = modify_pantry(
        uid=uid,
        ingredient_name=request.ingredient_name,
        amount=request.amount,
        action=request.action
    )
    if not success:
        raise HTTPException(status_code=400, detail="Updating Pantry failed.")

    return {"message": f"Pantry updated: {request.action.value} {request.amount} {request.ingredient_name}"}

@app.delete("/pantry/{uid}", status_code=204, tags=["Pantry"])
def delete_item_from_pantry(uid: int, ingredient_name: str, amount: int = 99999 ):
    """ Deletes item from user pantry using a Query Parameter. If no amount is given it will remove all. """
    success = modify_pantry(
        uid=uid,
        ingredient_name=ingredient_name,
        action=PantryAction.REMOVE)
    if not success: # if item is not in pantry 
        raise HTTPException(status_code=404, detail=f"Item '{ingredient_name}' not found in pantry of user {uid} or deletion failed.")
    return #  204 no content -> delete successful

# RECIPE ENDPOINTS

@app.post("/recipes", response_model=dict, status_code=201, tags=["Recipes"])
def add_recipe(recipe:Recipe):
    """Adds a new recipe to the database."""
    result = create_recipe(recipe)
    if result is False:
        raise HTTPException(status_code=400, detail="Could not create recipe.")
    return {"message": "Recipe created", "recipe_id": result}

@app.get("/recipes/{recipe_id}", response_model=Recipe, tags=["Recipes"])
def get_single_recipe(recipe_id: int):
    """Gets the recipe by the provided item ID."""
    recipe=get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return recipe

@app.get("/recipes", response_model=list[RecipeSummary], tags=["Recipes"])
def get_all_recipes(limit: int | None = None): 
    """
    Retrieves stored recipes.
    Optional Query Parameter:
    ?limit=10 -> Returns only the first 10 recipes.
    """
    recipes = get_all_recipes_summary()
    
    # Logic to handle the query parameter
    if limit:
        return recipes[:limit]
    
    return recipes



@app.put("/recipes/{recipe_id}", response_model=Recipe, tags=["Recipes"])
def update_existing_recipe(recipe_id: int, updated_recipe: Recipe):
    """Updates a specific existing recipe."""
    updated_recipe.recipe_id = recipe_id
    result = update_recipe(recipe_id, updated_recipe)
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found or update failed.")
    return result

# USER ENDPOINTS

@app.post("/users", response_model=User, status_code=201, tags=["Users"])
def create_new_user(user: User):
    """Adds a new user to the database."""
    created_user = create_user(user)
    print(created_user)
    if not created_user:
        raise HTTPException(status_code=400, detail="User could not be created.")
    return created_user

@app.get("/users/{uid}", response_model=User, tags=["Users"])
def read_user(uid:int):
    """Gets a user by the provided ID."""
    user = get_user_by_id(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@app.get("/users/search/{username}", response_model=User, tags=["Users"])
def read_user_by_name(username: str):
    """Gets user by user the provided name"""
    user=get_user_by_name(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@app.put("/users/{uid}", response_model=User, tags=["Users"])
def update_user_data(uid: int, user: User):
    """Updates the data of an existing user."""
    user.uid = uid
    updated_user = update_user(user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found or update failed.")
    return updated_user

# MATCHMAKING ENDPOINTS
@app.get("/matchmaking/{uid}", response_model=list[RecipeSummary], tags=["Matchmaking"])
def find_cookable(uid: int):
    """
    Returns a list of recipes that the user can cook 
    based on their current pantry inventory.
    """
    return get_cookable_recipes(uid)

@app.post("/cook/{uid}/{recipe_id}", tags=["Matchmaking"])
def cook_recipe_endpoint(uid: int, recipe_id: int):
    """
    Attempts to cook a recipe.
    - Verifies user has ingredients.
    - Subtracts amounts from pantry.
    """
    result = cook_recipe(uid, recipe_id)
    
    if result["status"] == "failed":
        # 400 Bad Request = Client Error (Not enough items)
        raise HTTPException(status_code=400, detail=result)
        
    if result["status"] == "error":
        # 500 Internal Server Error = Our fault
        raise HTTPException(status_code=500, detail=result["message"])
        
    return result