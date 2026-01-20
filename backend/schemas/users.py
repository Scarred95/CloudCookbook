"""
--------------------------------------------------------------------------------
Script Name:   users.py
Last Updated:  20/01/26

Description:
    This module defines the Data Transfer Objects (DTOs) and Data Schemas
    for all user-related content using Pydantic.

Key Features:
    - TODO
Dependencies:
    - pydantic (BaseModel, Field, field_validator, ConfigDict)
    - typing (Optional)
--------------------------------------------------------------------------------
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional

# --- Shared Properties ---

class UserBase(BaseModel):
    """base used by almost all other Schemas"""
    username: str = Field(...,min_length=3,max_length=30,examples=["Max Mueller"])
    active: bool = True
    
    @field_validator('username', mode='before') # changes Username to Lowercase in the DB.
    @classmethod
    def enforce_lowercase(cls, value: str) -> str:
        if isinstance(value, str):
            return value.lower().strip()
        return value
    
# --- CREATE / POST SCHEMA --- 
class UserCreate(UserBase):
    """used to create, adds a Password field"""
    password: str = Field(..., min_length=8, examples=["SecurePass123!"])


# --- UPDATE / PUT|PATCH SCHEMA ---
class UserUpdate(BaseModel):
    """used when updating, has all fields optional."""
    username: str | None = Field(None, min_length=3, max_length=30)
    password: str | None = Field(None, min_length=8)
    active: bool | None = None

# --- RESPONSE / GET SCHEMA ---
class User(UserBase):
    """used when getting a User."""
    id: int  # User ID - Primary Key in DB
    member_since: str | None = None
    model_config = ConfigDict(from_attributes=True)
