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
        "Based on an application description and provided database generation instructions, you will create an appropriate "
        "database schema and implementation for a Next.js project.\n\n"
        
        "Your task is to:\n"
        "1. Analyze the application description and provided database generation instructions and understand what data needs to be stored\n"
        "2. Design an appropriate SQLite database schema with tables, relationships, and indices\n"
        "3. Create queries for the database to be used in the API routes\n"
        "4. Design API routes for interacting with the database\n\n"
        
        "Your output should include:\n"
        "- A complete SQL schema file with tables, indices, triggers and sample data\n"
        "- Database utility code for the application\n"
        "- Content for API routes that access the database\n\n"
        
        "IMPORTANT NEXT.JS API ROUTING GUIDELINES:\n"
        "This project uses Next.js 12 with the Pages Router (not App Router). Follow these specific API routing rules:\n"
        "1. Next.js 12 API routes should follow RESTful naming conventions with singular resource names (e.g., user.js, product.js)\n"
        "2. For handling ID-based requests, create logic like this inside a single API file:\n"
        "   - Check for ID in request.query (e.g., if (req.query.id) { /* handle single item */ })\n"
        "   - Use the same file for both collection and single item operations\n"
        "3. DO NOT create nested folder structures with bracket notation like 'pages/api/[resource]/[id].js'\n"
        "4. Instead, create ONE API file per resource. For example (these are just examples):\n"
        "   - 'pages/api/product.js' that handles both GET /api/product (all products) and GET /api/product?id=123 (single product)\n"
        "   - 'pages/api/user.js' that handles both GET /api/user (all users) and GET /api/user?id=456 (single user)\n"
        "   -  IMPORTANT: YOUR TOOL USES A RELATIVE PATH FROM THE PAGES FOLDER SO IT IS STRICTLY FORBIDDEN TO USE A PAGES IN THE PATH"
        "5. Frontend pages should call these APIs using patterns like (examples only):\n"
        "   - For all items: fetch('/api/product')\n"
        "   - For a single item: fetch(`/api/product?id=${id}`)\n"
        "6. Make sure all exported handler functions parse and validate query parameters properly\n\n"
        
        "IMPORTANT FILE PATH GUIDELINES:\n"
        "- DATABASE FILES:\n"
        "  - All database-related files must be placed within the 'db/' directory\n"
        "  - Place database schema in 'db/schema.sql'\n"
        "  - Place database sample data in 'db/sample_data.sql'\n"
        "  - Place a reset js script in 'db/reset.js' that resets the database to the sample data\n"
        "  - When called, the reset.js script should remove any existing database files and then create a new one with the sample data\n"
        "  - The reset.js is called automatically so you should not call it ANYWHERE in your code\n"
        "  - Place database connection code in 'db/connection.js'\n"
        "  - Place database queries in 'db/queries.js'\n"
        "  - You may create additional subdirectories within 'db/' as needed\n\n"
        "  - ALWAYS USE CONNECTION.JS TO CONNECT TO THE DATABASE\n"
        
        "- API ROUTES:\n"
        "  - All API routes must be placed in 'pages/api/' directory\n"
        "  - API routes are server-side endpoints, not frontend pages\n"
        "  - API routes must import database utilities using relative paths (e.g., '../../db/connection.js')\n"
        "  - API routes should always use the queries from the queries.js file\n"
        "  - API routes should be well documented with JSDoc comments for each handler function\n"
        "  - API routes should throw errors if the database connection fails or if the query fails and it should be logged to the console.\n"
        "  - Include proper error handling with appropriate HTTP status codes (400, 404, 500, etc.)\n\n"

        "FILE ACCESS RESTRICTIONS:\n"
        "- You can only read and write files in the 'db/' and 'pages/api/' directories\n"
        "- You cannot access files outside these directories\n"
        "- When creating directories, they must be within these allowed paths\n\n"
        
        "IMPORTANT EXPORT GUIDELINES:\n"
        "- In connection.js: Export the database instance as default export\n"
        "- In queries.js: Export all query functions as named exports\n"
        "- All API routes must export a default function handler that routes requests based on method and query parameters\n"
        "- Include proper JSDoc comments for all exports\n\n"
        
        "When creating files, use the write_file tool with the appropriate path. "
        "You can list existing files with list_available_files and read file content with read_file_content.\n"
        "BE SURE TO LIST AVAILABLE FILES AND READ FILE CONTENTS BEFORE WRITING FILES TO GET AN ACCURATE IDEA OF THE LOGIC THAT ALREADY EXISTS. "
        "If you need to create directories, use the create_directory tool.\n\n"

        "ALWAYS USE COMMONJS MODULE SYNTAX (require/module.exports) not ES modules (import/export).\n\n"       

        "Note: You cannot use ANY additional npm packages, outside of the following which are already installed: "
        "  - sqlite3"
        "  - next"
        "  - react"
        "  - react-dom"
        "  - react-router-dom"

        "Images: If you need to use images as examples, use the following format: https://placehold.co/600x400&text=text_here"

        "ONLY MAKE CHANGES IF NECESSARY. IF THE CODE EXISTS AND THERE ARE NO ISSUES GIVEN, DO NOT MAKE ANY CHANGES."
        ),

        tools=[
            list_available_files,
            read_file_content,
            write_file,
            create_directory
        ],
    )
    
    return sqlite_agent