import subprocess
import os
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal, Any
import json
import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv; load_dotenv()

from .context import CodeGenerationDeps, SQLiteConfigOutput

from tools.database.list_available_files import list_available_files
from tools.database.read_file_content import read_file_content
from tools.database.write_file import write_file
from tools.database.create_directory import create_directory


# =======================
# SQLite Agent Definition
# =======================

def create_sqlite_agent():
    """Creates an agent specialized in designing and implementing SQLite databases for Next.js"""

    sqlite_agent = Agent(
        deps_type=CodeGenerationDeps,
        result_type=SQLiteConfigOutput,
        system_prompt = (
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
        "- Content for API routes that access the database\n\n"
        
        "IMPORTANT FILE PATH GUIDELINES:\n"
        "- DATABASE FILES:\n"
        "  - All database-related files must be placed within the 'db/' directory\n"
        "  - Place database schema in 'db/schema.sql'\n"
        "  - Place database connection code in 'db/connection.js'\n"
        "  - Place database queries in 'db/queries.js'\n"
        "  - You may create additional subdirectories within 'db/' as needed\n\n"
        
        "- API ROUTES:\n"
        "  - All API routes must be placed in 'pages/api/' or 'api/' (both refer to the same location)\n"
        "  - You can specify paths either as 'pages/api/users.js' or as 'api/users.js'\n"
        "  - API routes are server-side endpoints, not frontend pages\n"
        "  - API routes must import database utilities using relative paths (e.g., '../../db/connection.js')\n\n"
        
        "FILE ACCESS RESTRICTIONS:\n"
        "- You can only read and write files in the 'db/' and 'pages/api/' directories\n"
        "- You cannot access files outside these directories\n"
        "- When creating directories, they must be within these allowed paths\n\n"
        
        "IMPORTANT EXPORT GUIDELINES:\n"
        "- In connection.js: Export the database instance as default export\n"
        "- In queries.js: Export all query functions as named exports\n"
        "- All API routes must export a default function\n"
        "- Include proper JSDoc comments for all exports\n\n"
        
        "When creating files, use the write_file tool with the appropriate path. "
        "You can list existing files with list_available_files and read file content with read_file_content. "
        "If you need to create directories, use the create_directory tool.\n\n"
        
        "You may be provided information about existing files to help align your database design "
        "with the application structure and requirements."
        ),

        tools=[
            list_available_files,
            read_file_content,
            write_file,
            create_directory
        ],
    )
    
    return sqlite_agent