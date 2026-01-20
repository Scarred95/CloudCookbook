"""
--------------------------------------------------------------------------------
Script Name:   pydantic_models.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-15

Description:
    This module defines the Data Transfer Objects (DTOs) and Data Schemas
    for the entire application using Pydantic.

    It serves as the "Contract" between the API Layer and the Database Layer,
    ensuring strict type validation (e.g., string lengths, numeric ranges)
    before data is processed or stored.

Key Features:
    - Core Models: Defines standard entities like 'User', 'Recipe', and 'Item'.
    - DTOs: Specialized models for specific API requests (e.g., 'ItemCreateRequest')
      or summarized list views (e.g., 'RecipeSummary').
    - Enums: Standardizes fixed choices like 'PantryAction' (ADD/REMOVE).
    - Validation: Enforces constraints (e.g., time_needed > 0, max lengths) as well as enforcement of lowercase.

Dependencies:
    - pydantic (BaseModel, Field)
    - enum
--------------------------------------------------------------------------------
"""

from pydantic import BaseModel, Field, field_validator
from enum import Enum

class PantryAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"

# --- USER MODELS ---

class User(BaseModel):
    # | -> means OR. This makes the id optional as new users don't have an ID yet
    uid: int | None = None 
    username: str = Field(..., min_length=3, max_length=30, examples=["Max Mueller"])
    active: int = Field(..., ge=0, le=1) # 1 = active, 0 = inactive
    member_since: str | None = None # Set to None as new users may not have the Timestamp yet

# --- ITEM MODELS ---

class Item(BaseModel):
    # -1 means NOT SET
    ingredient_id: int | None = -1
    ingredient_name: str = Field(..., min_length=3, max_length=30, examples=["Rice"])
    
    @field_validator('ingredient_name', mode='before')
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value


class ItemCreateRequest(BaseModel):
    """Specific model for POST /items requests"""
    ingredient_name: str

    @field_validator('ingredient_name', mode='before')
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value

# --- PANTRY MODELS ---

class PantryModifyRequest(BaseModel):
    """Specific model for pantry requests"""
    ingredient_name: str
    amount: int = Field(..., gt=0, examples=[500])
    action: PantryAction

    @field_validator('ingredient_name', mode='before')
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value

# --- RECIPE MODELS ---

class Recipe(BaseModel):
    recipe_id: int | None = None
    recipe_name:str = Field(...,min_length=3,max_length=50,examples=["Mushroom Stew"])
    description: str = Field(..., max_length=200, examples=["Ein deftiger Eintopf für kalte Tage."])
    recipe_creator: int | None = None
    time_needed: int = Field(..., gt=0, le=600, examples=[45]) 
    
    # Dict keys are Strings (Ingredient Name), Values are Ints (Amount)
    recipe_ingredients: dict[str, int] = Field(..., examples=[{"fish fillet": 5, "rice": 100}])
    instructions: list[str] = Field(..., examples=[["Slice the vegetables", "Boil water"]])

    # 1. CLEAN THE RECIPE NAME
    @field_validator('recipe_name', mode='before')
    @classmethod
    def clean_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value

    # 2. CLEAN THE INSTRUCTIONS
    @field_validator('instructions', mode='before')
    @classmethod
    def clean_instruction_list(cls, value: list) -> list:
        if isinstance(value, list):
            # Apply logic to every string in the list
            return [item.lower().strip() for item in value if isinstance(item, str)]
        return value
    
    # 3. CLEAN THE INGREDIENTS
    @field_validator('recipe_ingredients', mode='before')
    @classmethod
    def clean_ingredient_keys(cls, value: dict) -> dict:
        if isinstance(value, dict):
            # Clean Key (k), keep Value (v)
            return {k.lower().strip(): v for k, v in value.items() if isinstance(k, str)}
        return value

class RecipeSummary(BaseModel):
    """Lighter model for Lists/Dashboards (No heavy ingredients/steps)"""
    recipe_id: int
    recipe_name: str
    description: str | None = None
    recipe_creator: int | None = None
    time_needed: int
    
    @field_validator('recipe_name', mode='before')
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip() 
        return value