"""
--------------------------------------------------------------------------------
Script Name:   db_user.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16

Description:
    This module handles the database logic for User Management.
    It manages the 'user' table, providing CRUD operations (Create, Read, Update)
    and converting between SQLite rows and Pydantic User objects.

Key Features:
    - create_user: Inserts a new user with automatic timestamp generation.
    - get_user_by_id / get_user_by_name: Flexible retrieval methods.
    - update_user: Dynamically updates only the changed fields (Partial Update),
      while protecting immutable fields like 'member_since'.

Dependencies:
    - sqlite3
    - pydantic_models (User class)
    - datetime
--------------------------------------------------------------------------------
"""

import sqlite3
from models.pydantic_models import User
from datetime import datetime
from helper.logger import logger, sql_logger

database = "cloudcookbook.db"

def create_user(user: User) -> User | None:
    """Inserts a new user into the 'users' table."""
    logger.debug(f"Starting create_user for: {user.username}")
    conn = None # initialize for safety in finally block
    if user.member_since is None: # set current date if 'member_since' is not provided
        user.member_since = datetime.today().strftime('%d.%m.%Y')

    sql_insert = """
        INSERT INTO user ( active, username, member_since)
        VALUES (?,?,?)
    """
    
    try:
        conn = sqlite3.connect(database)
        with conn: # automatically manages transaction commit/rollback
            cursor = conn.cursor()
            params = (user.active, user.username, user.member_since)
            sql_logger.info(f"Query: {sql_insert} | Params: {params}")
            cursor.execute(sql_insert, params)
            user.uid = cursor.lastrowid
            logger.info(f"Successfully created User '{user.username}' (UID: {user.uid})")
            return user

    except sqlite3.IntegrityError as e: # handles unique constraint violations
        logger.warning(f"Integrity Error creating user '{user.username}' (Duplicate?): {e}")
        return None

    except sqlite3.Error as e:
        logger.error(f"Database Error in create_user: {e}", exc_info=True)
        return None
    finally: # ensure the database connection is closed regardless of success/failure
        conn.close()

def get_user_by_id(uid: int) -> User | None:
    """Gets user by provided user id"""
    logger.debug(f"Starting get_user_by_id for UID: {uid}")

    conn = None # initialize for safety in finally block
    sql_select = "SELECT uid, active, username, member_since FROM user WHERE uid = ?"

    try:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row # allows accessing columns by name
        with conn: # automatically manages transaction commit/rollback
            cursor = conn.cursor()
            sql_logger.info(f"Query: {sql_select} | Params: {(uid,)}")
            cursor.execute(sql_select, (uid,))
            row = cursor.fetchone()
        
        if row:
            logger.debug(f"Found User for UID {uid}")
            user_data = dict(row) # convert sqlite.Row object to a standard Python dictionary
            return User(**user_data) # instantiate Pydantic model from dictionary data
        else:
            logger.debug(f"No User found for UID {uid}")
            return None
    except sqlite3.Error as e: 
        logger.error(f"Error fetching user {uid}: {e}", exc_info=True)
        return None
    finally: # ensure the database connection is closed regardless of success/failure
        if conn:
            conn.close()

def get_user_by_name(username: str) -> User | None:
    """Gets a user by provided username."""
    logger.debug(f"Starting get_user_by_name for: {username}")
    sql_select = "SELECT uid, active, username, member_since FROM user WHERE username = ?"

    try:
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row # allows accessing columns by name
        with conn: #automatically manages transaction commit/rollback
            cursor = conn.cursor()
            sql_logger.info(f"Query: {sql_select} | Params: {(username,)}")
            cursor.execute(sql_select, (username,))
            row = cursor.fetchone()

        if row:
            logger.debug(f"Found User for username '{username}'")
            user_data = dict(row) # convert sqlite.Row object to a standard Python dictionary
            return User(**user_data) # instantiate Pydantic model from dictionary data
        else:
            logger.debug(f"No User found for username '{username}'")
            return None

    except sqlite3.Error as e:
        logger.error(f"Error fetching username '{username}': {e}", exc_info=True)
        return None
    finally: # ensure the database connection is closed regardless of success/failure
        if conn:
            conn.close()

def update_user(user: User) -> User | None:
    """Updates the data of existing users."""
    logger.debug(f"Starting update_user for UID: {user.uid}")
    changes = user.model_dump(exclude_none=True) # extract only fields that are NOT None and NOT 'uid'/'member_since'
    uid = changes.pop('uid', None) # remove fields designated for the WHERE clause and exclusions
    changes.pop('member_since', None) # the 'member_since' field must NOT be updated
    if not uid or not changes:
        logger.warning(f"Update aborted for User {uid}: No valid changes provided.")
        return None
    keys = changes.keys() # get keys to dynamically build the SET part of the query
    set_statements = ", ".join([f"{key} = ?" for key in keys]) 
    sql_update = f"UPDATE user SET {set_statements} WHERE uid = ?"
    params = list(changes.values())
    params.append(uid) # add the UID to the end of parameters for the WHERE clause

    try:
        conn = sqlite3.connect(database)
        with conn: # automatically manages transaction commit/rollback
            cursor = conn.cursor()
            sql_logger.info(f"Query: {sql_update} | Params: {params}")
            cursor.execute(sql_update, tuple(params)) 
            
            if cursor.rowcount == 0: # check if any rows were affected
                logger.warning(f"Update failed: User with UID {uid} not found.")
                return None
            
            logger.info(f"Successfully updated User {uid}. Fields: {list(keys)}")
            return user 

    except sqlite3.Error as e:
        logger.error(f"Database Error in update_user: {e}", exc_info=True)
        return None
    finally: # ensure the database connection is closed regardless of success/failure
        if conn:
            conn.close()