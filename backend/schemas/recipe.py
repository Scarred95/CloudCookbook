"""
--------------------------------------------------------------------------------
Script Name:   recipe.py
Last Updated:  20/01/26

Description:
    This module defines the Data Transfer Objects (DTOs) and Data Schemas
    for all Recipe-related content using Pydantic.

Key Features:
    - TODO
Dependencies:
    - pydantic (BaseModel, Field, field_validator, ConfigDict)
    - typing (List, Dict, Optional)
--------------------------------------------------------------------------------
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Optional

# --- HELPER SCHEMAS ---

class IngredientEntry(BaseModel):
    """used when listing ingredients inside a Recepie Response"""
    name: str
    amount: int
    unit: Optional[str] = "grams" # Future-proofing
    

# --- SHARED SCHEMAS ---
class RecipeBase(BaseModel):
    recipe_name: str = Field(..., min_length=3, max_length=50, examples=["Mushroom Stew"])
    description: str = Field(..., max_length=200)
    time_needed: int = Field(..., gt=0, le=600, examples=[45])

    # Validators from your old code (Cleaning input)
    @field_validator('recipe_name', mode='before')
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value

# --- CREATE SCHEMA ---

class RecipeCreate(RecipeBase):
    # Input: {"flour": 500, "sugar": 100}
    recipe_ingredients: Dict[str, int] = Field(..., examples=[{"fish fillet": 5, "rice": 100}])
    instructions: List[str] = Field(..., examples=[["Slice the vegetables", "Boil water"]])

    @field_validator('instructions', mode='before')
    @classmethod
    def clean_instructions(cls, value: List[str]) -> List[str]:
        if isinstance(value, list):
            return [item.lower().strip() for item in value if isinstance(item, str)]
        return value

    @field_validator('recipe_ingredients', mode='before')
    @classmethod
    def clean_ingredients(cls, value: Dict[str, int]) -> Dict[str, int]:
        if isinstance(value, dict):
            return {k.lower().strip(): v for k, v in value.items() if isinstance(k, str)}
        return value

# Update shall be made in Logic - Assume its a new recipe, compare ith the one to be updatet, only change different fields.

# --- RESPONSE SCHEMA ---
class Recipe(RecipeBase):
    id: int  # Standardize to 'id'
    creator_id: int
    instructions: List[str]
    recipe_ingredients: Dict[str, int] 

    model_config = ConfigDict(from_attributes=True)
    
class RecipeSummary(BaseModel):
    id: int
    recipe_name: str
    description: Optional[str] = None
    time_needed: int
    creator_id: int

    model_config = ConfigDict(from_attributes=True)
