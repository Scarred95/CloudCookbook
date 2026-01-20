"""
--------------------------------------------------------------------------------
Script Name:   items.py
Last Updated:  20/01/26

Description:
    This module defines the Data Transfer Objects (DTOs) and Data Schemas
    for all Ingredient-related content using Pydantic.

Key Features:
    - TODO
Dependencies:
    - pydantic (BaseModel, Field, field_validator, ConfigDict)
    - typing (Optional)
--------------------------------------------------------------------------------
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional

# --- SHARED SCHEMAS ---

class ItemBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, examples=["Rice"])

    @field_validator('name', mode='before')
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value
    
# --- CREATE SCHEMAS ---
class ItemCreate(ItemBase):
    pass # No extra fields needed for creation

# --- RESPONSE SCHEMAS ---
class Item(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# --- UPDATE SCHEMAS ---
class ItemUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, min_length=3, max_length=50)