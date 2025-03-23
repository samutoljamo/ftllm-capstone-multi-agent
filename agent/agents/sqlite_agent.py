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

from .context import SQLiteConfigInput, SQLiteConfigOutput

from tools.database.list_available_files import list_available_files
from tools.database.read_file_content import read_file_content
from tools.database.write_file import write_file
from tools.database.create_directory import create_directory
from tools.database.get_file_template import get_file_template
from tools.database.validate_file_path import validate_file_path


# =======================
# SQLite Agent Definition
# =======================

def create_sqlite_agent(ai_model):
    """Creates an agent specialized in designing and implementing SQLite databases for Next.js"""
    
    sqlite_agent = Agent(
        result_type=SQLiteConfigOutput,
        tools=[
            list_available_files,
            read_file_content,
            write_file,
            create_directory,
            get_file_template,
            validate_file_path
        ],
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
        )
    )
    
    return sqlite_agent