"""
--------------------------------------------------------------------------------
Script Name:   logger.py
Project:       CloudCookbook (Team 2 - Appelt, Nguyen, Hoppen)
Last Updated:  2025-12-16
Description:   Centralized Logging.
               Creates a 'logs/' directory and saves output there.
--------------------------------------------------------------------------------
"""
import logging
import sys
import os

# --- 0. SETUP LOG DIRECTORY ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
    print(f"Created logging directory: {LOG_DIR}")


# --- 1. MAIN APPLICATION LOGGER ---
# Create the Logger
logger = logging.getLogger("CloudCookbook")
logger.setLevel(logging.DEBUG) # Capture everything from Debug upwards

# Create the Formatter
# %(asctime)s: Adds the timestamp
# %(levelname)-8s: Adds the level (INFO, ERROR)
# %(module)s: Tells which file
standard_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s.%(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
sql_formatter = logging.Formatter('%(asctime)s | SQL_TRACE | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
api_formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create The File Handler
# mode='a' (Append): Add to the bottom of the file.
# setLevel(logging.INFO): This is a Filter."Ignore the noisy DEBUG stuff. Only save important events"
log_file_path = os.path.join(LOG_DIR, "cloud_cookbook.log")
file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
file_handler.setFormatter(standard_formatter)
file_handler.setLevel(logging.INFO)

# Create The Console Handler
# sys.stdout: Terminal Window
# setLevel(logging.DEBUG): This allows everything through.

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(standard_formatter)
console_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --- 2. SQL AUDIT LOGGER ---
# This logger exists ONLY to write raw SQL commands to a separate file
sql_logger = logging.getLogger("SQL_Tracer")
sql_logger.setLevel(logging.INFO)
# SQL File Handler
sql_file_path = os.path.join(LOG_DIR, "sql_audit.log")
sql_handler = logging.FileHandler(sql_file_path, mode='a', encoding='utf-8')
sql_handler.setFormatter(sql_formatter)
sql_logger.addHandler(sql_handler)

# --- 3. API AUDIT LOGGER ---
# This logger exists ONLY to write raw SQL commands to a separate file
api_logger = logging.getLogger("API_Access")
api_logger.setLevel(logging.INFO)

# Tracks every incoming HTTP request, status code, and processing time
api_logger = logging.getLogger("API_Access")
api_logger.setLevel(logging.INFO)

# Formatter: Timestamp | METHOD | PATH | STATUS | DURATION
api_formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# File Handler
api_file_path = os.path.join(LOG_DIR, "api_access.log")
api_handler = logging.FileHandler(api_file_path, mode='a', encoding='utf-8')
api_handler.setFormatter(api_formatter)
api_logger.addHandler(api_handler)

# Usage:
# from logger_config import logger, sql_logger, api_logger

"""Usage in Functions:
Logging SQL Query's before the EXECUTE:
->sql_logger.info(f"Query: {sql_string} | Params: {params}")

Debug Data for what was done:
-> logger.debug(f"Fetching data for ID: {id}") 
-> logger.debug(f"No data found for ID: {id}")


State Data for the Log:
-> logger.info(f"Successfully finished operation on: {input_data}")
-> logger.info(f"Failed operation on: {input_data}")

Logging Error's
-> logger.error(f"Critical DB Failure in your_write_function: {e}", exc_info=True)


Examples:
Modify Pantry:
-Entry:
->logger.debug(f"User {uid} modifying pantry: {action} {amount}x {ingredient_name}")
-Success:
->logger.info(f"Pantry Update: User {uid} {action.value}ed {amount} of '{ingredient_name}'")
-Failure:
->logger.error(f"Pantry Update Failed: User {uid} {action.value}ed {amount} of '{ingredient_name}'")
"""