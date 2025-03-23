from agents.context import SQLiteDeps
from agents.context import SQLiteConfigOutput

from pydantic import BaseModel
from typing import List, Dict, Optional
from pydantic_ai import Agent
from tools.sqlite_db_file_content import read_file_content
from tools.sqlite_db_list_files import list_available_files
from tools.sqlite_db_create_dir import create_directory
from tools.sqlite_db_template import get_file_template
from tools.sqlite_db_path import validate_file_path
from tools.sqlite_db_write_file import write_file


# Define the sqlite agent directly without a creation function
sqlite = Agent(
    deps_type=SQLiteDeps,
    result_type=SQLiteConfigOutput,
    system_prompt=(
        "You are an expert in designing and implementing SQLite databases for Next.js applications. "
        "Based on an application description and optional existing files, you will create an appropriate "
        "database schema and implementation for a Next.js project.\n\n"
        
        "Your task is to:\n"
        "1. Analyze the application description and understand what data needs to be stored\n"
        "2. Design an appropriate SQLite database schema with tables, relationships, and indices\n"
        "3. Create utility files for database access including queries and helper functions\n"
        "4. Design API routes for interacting with the database\n\n"
        
        "Your output should include:\n"
        "- A complete SQL schema file with tables, indices, triggers and sample data\n"
        "- Database utility code for the application\n"
        "- A list of files to be created\n"
        "- Content for API routes\n\n"
        
        "IMPORTANT FILE PATH GUIDELINES:\n"
        "- Always place database schema in '/db/schema.sql'\n"
        "- Always place database connection code in '/lib/db.js'\n"
        "- Always place database queries in '/lib/db-queries.js'\n"
        "- Place API routes in '/pages/api/[resource].js' format\n"
        "- Use relative imports in your code (e.g., '../../lib/db.js')\n\n"
        
        "IMPORTANT EXPORT GUIDELINES:\n"
        "- In db.js: Always export the database instance as default export\n"
        "- In db-queries.js: Export all query functions as named exports\n"
        "- Ensure all API routes export a default function\n"
        "- Include proper JSDoc comments for all exports\n\n"
        
        "You may be provided information about existing files to help align your database design "
        "with the application structure and requirements. Use this information to tailor your database "
        "design appropriately."
    ),
    tools=[
        read_file_content
    ]
    
) 