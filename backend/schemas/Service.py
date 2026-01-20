"""
--------------------------------------------------------------------------------
Script Name:   Service.py
Last Updated:  20/01/26

Description:
    This module defines the Data Transfer Objects (DTOs) and Data Schemas
    for all Service-related content using Pydantic.

Key Features:
    - TODO
Dependencies:
    - pydantic (BaseModel, Field, field_validator, ConfigDict)
    - enum (Enum)
    - typing (Optional)
--------------------------------------------------------------------------------
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from typing import Optional

# --- ENUMS ---
class PantryAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    
# --- PANTRY ITEM RESPONSE SCHEMA ---

class PantryItemResponse(BaseModel):
    """
    Represents a single row in the user's pantry.
    Includes the joined Ingredient Name for convenience.
    """
    ingredient_id: int
    ingredient_name: str # Joined from Item table
    amount: int

    model_config = ConfigDict(from_attributes=True)
    
# --- PANTRY MODIFY SCHEMA ---
class PantryModifyRequest(BaseModel):
    ingredient_name: str = Field(..., min_length=2, examples=["Milk"])
    amount: int = Field(..., gt=0, examples=[1000])
    action: PantryAction = Field(..., examples=[PantryAction.ADD])

    @field_validator('ingredient_name', mode='before')
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value
    
# --- COOKING SCHEMA ---
class CookingRequest(BaseModel):
    """
    Used when a user clicks 'Cook This'.
    Allows us to pass extra options later (e.g., 'substitute_missing=True')
    """
    uid: int # User-ID to get the user's Pantry
    recipe_id: int
    servings: int = 1 # Logic can multiply ingredients by this amount