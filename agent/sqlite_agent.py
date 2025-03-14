import subprocess
import os
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal, Any
import json
import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits, Usage
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv; load_dotenv()



# =======================
# Data Models for SQLite Agent
# =======================

class SQLiteConfigInput(BaseModel):
    """Input configuration for SQLite agent"""
    app_description: str  # Description of the app to create a database for
    existing_files: Optional[List[str]] = None  # List of existing file paths to analyze
    file_contents: Optional[Dict[str, str]] = None  # Contents of files to analyze
    include_auth: bool = True
    include_session: bool = True
    database_name: str = "app.db"
    path_templates: Optional[Dict[str, str]] = None  # Templates for standard file paths

class SQLiteConfigOutput(BaseModel):
    """Output from SQLite agent"""
    success: bool  # Whether the operation was successful
    message: str  # Success or error message
    created_files: List[str]  # List of files created
    schema_content: Optional[str] = None  # SQL schema for the database
    db_utils_content: Optional[str] = None  # Content for db-queries.js
    api_routes: Optional[Dict[str, str]] = None  # API routes for database interaction

# =======================
# SQLite Agent Definition
# =======================

def create_sqlite_agent(ai_model):
    """Creates an agent specialized in designing and implementing SQLite databases for Next.js"""
    
    sqlite_agent = Agent(
        ai_model,
        deps_type=SQLiteConfigInput,
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
        )
    )
    
    # Add tools for the SQLite agent to analyze files and structure
    @sqlite_agent.tool
    async def read_file_content(ctx: RunContext[SQLiteConfigInput], file_path: str) -> str:
        """
        Read the content of a file in the project.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Content of the file, or empty string if not found/provided
        """
        if ctx.deps.file_contents and file_path in ctx.deps.file_contents:
            return ctx.deps.file_contents[file_path]
        return ""
    
    @sqlite_agent.tool
    async def list_available_files(ctx: RunContext[SQLiteConfigInput]) -> List[str]:
        """
        List all available files that can be analyzed.
        
        Returns:
            List of file paths that can be read
        """
        if ctx.deps.existing_files:
            return ctx.deps.existing_files
        return []
    


    @sqlite_agent.tool
    async def write_file(ctx: RunContext[SQLiteConfigInput], file_path: str, content: str) -> str:
        """
        Write content to a file in the project.
        
        Args:
            file_path: Path where the file should be written
            content: Content to write to the file
            
        Returns:
            Success message or error
        """
        try:
            # This doesn't actually write the file yet, it just stores it for later use
            # We'll collect all the files the agent wants to write and implement them later
            if not hasattr(ctx, 'files_to_write'):
                ctx.files_to_write = {}
            
            ctx.files_to_write[file_path] = content
            return f"File {file_path} will be created"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @sqlite_agent.tool
    async def create_directory(ctx: RunContext[SQLiteConfigInput], directory_path: str) -> str:
        """
        Create a directory in the project.
        
        Args:
            directory_path: Path to the directory to create
            
        Returns:
            Success message or error
        """
        try:
            # This doesn't actually create the directory yet, it just notes it for later
            if not hasattr(ctx, 'directories_to_create'):
                ctx.directories_to_create = []
            
            ctx.directories_to_create.append(directory_path)
            return f"Directory {directory_path} will be created"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @sqlite_agent.tool
    async def get_file_template(ctx: RunContext[SQLiteConfigInput], file_type: str) -> str:
        """
        Get a template for a specific type of file with proper exports.
        
        Args:
            file_type: Type of file to get template for ('db', 'queries', 'api')
            
        Returns:
            Template code with proper structure and exports
        """
        database_name = ctx.deps.database_name
        
        templates = {
            "db": f"""// Database connection module for {database_name}
import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

// Ensure the data directory exists
const dataDir = path.join(process.cwd(), 'data');
if (!fs.existsSync(dataDir)) {{
  fs.mkdirSync(dataDir, {{ recursive: true }});
}}

// Database file path
const dbPath = path.join(dataDir, '{database_name}');

/**
 * SQLite database instance
 * @type {{Database}}
 */
const db = new Database(dbPath);

// Enable foreign keys
db.pragma('foreign_keys = ON');

// Initialize database if needed
const initializeDatabase = () => {{
  const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").all();
  
  if (tables.length === 0) {{
    // Read and execute the schema file
    const schemaPath = path.join(process.cwd(), 'db', 'schema.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');
    
    // Split by semicolon to execute each statement separately
    schema.split(';').forEach(statement => {{
      if (statement.trim()) {{
        db.prepare(statement).run();
      }}
    }});
    
    console.log('Database initialized with schema');
  }}
}};

// Initialize on import
initializeDatabase();

// Export the database instance
export default db;
""",
            "queries": """// Database queries module
import db from './db';

/**
 * Get all items from a table
 * @param {string} tableName - Name of the table to query
 * @returns {Array} Array of items
 */
export function getAll(tableName) {
  const stmt = db.prepare(`SELECT * FROM ${tableName}`);
  return stmt.all();
}

/**
 * Get a single item by ID
 * @param {string} tableName - Name of the table to query
 * @param {number} id - ID of the item to get
 * @returns {Object|null} The item or null if not found
 */
export function getById(tableName, id) {
  const stmt = db.prepare(`SELECT * FROM ${tableName} WHERE id = ?`);
  return stmt.get(id);
}

/**
 * Insert a new item
 * @param {string} tableName - Name of the table to insert into
 * @param {Object} data - Data to insert
 * @returns {Object} Result with the inserted ID
 */
export function insert(tableName, data) {
  // Create placeholders and values array
  const keys = Object.keys(data);
  const placeholders = keys.map(() => '?').join(', ');
  const values = keys.map(key => data[key]);
  
  const stmt = db.prepare(`INSERT INTO ${tableName} (${keys.join(', ')}) VALUES (${placeholders})`);
  const result = stmt.run(...values);
  
  return {
    id: result.lastInsertRowid,
    changes: result.changes
  };
}

/**
 * Update an existing item
 * @param {string} tableName - Name of the table to update
 * @param {number} id - ID of the item to update
 * @param {Object} data - Data to update
 * @returns {Object} Result with number of changes
 */
export function update(tableName, id, data) {
  // Create set clause
  const keys = Object.keys(data);
  const setClause = keys.map(key => `${key} = ?`).join(', ');
  const values = [...keys.map(key => data[key]), id];
  
  const stmt = db.prepare(`UPDATE ${tableName} SET ${setClause} WHERE id = ?`);
  const result = stmt.run(...values);
  
  return {
    changes: result.changes
  };
}

/**
 * Delete an item by ID
 * @param {string} tableName - Name of the table to delete from
 * @param {number} id - ID of the item to delete
 * @returns {Object} Result with number of changes
 */
export function deleteById(tableName, id) {
  const stmt = db.prepare(`DELETE FROM ${tableName} WHERE id = ?`);
  const result = stmt.run(id);
  
  return {
    changes: result.changes
  };
}
""",
            "api": """// API route template
import { getAll, getById, insert, update, deleteById } from '../../lib/db-queries';

/**
 * API handler for [resource]
 * 
 * @param {import('next').NextApiRequest} req - The request object
 * @param {import('next').NextApiResponse} res - The response object
 */
export default async function handler(req, res) {
  const { method } = req;
  const tableName = '[TABLE_NAME]'; // Replace with actual table name
  
  try {
    switch (method) {
      case 'GET':
        // Get all items or a specific item by ID
        const { id } = req.query;
        if (id) {
          const item = getById(tableName, id);
          if (!item) {
            return res.status(404).json({ error: 'Item not found' });
          }
          return res.status(200).json(item);
        } else {
          const items = getAll(tableName);
          return res.status(200).json(items);
        }
        
      case 'POST':
        // Create a new item
        const result = insert(tableName, req.body);
        return res.status(201).json({ id: result.id, ...req.body });
        
      case 'PUT':
        // Update an existing item
        const { id: updateId } = req.query;
        if (!updateId) {
          return res.status(400).json({ error: 'ID is required' });
        }
        
        const updateResult = update(tableName, updateId, req.body);
        if (updateResult.changes === 0) {
          return res.status(404).json({ error: 'Item not found' });
        }
        
        return res.status(200).json({ id: updateId, ...req.body });
        
      case 'DELETE':
        // Delete an item
        const { id: deleteId } = req.query;
        if (!deleteId) {
          return res.status(400).json({ error: 'ID is required' });
        }
        
        const deleteResult = deleteById(tableName, deleteId);
        if (deleteResult.changes === 0) {
          return res.status(404).json({ error: 'Item not found' });
        }
        
        return res.status(200).json({ success: true });
        
      default:
        res.setHeader('Allow', ['GET', 'POST', 'PUT', 'DELETE']);
        return res.status(405).json({ error: `Method ${method} Not Allowed` });
    }
  } catch (error) {
    console.error('API error:', error);
    return res.status(500).json({ error: 'Internal Server Error' });
  }
}
"""
        }
        
        if file_type in templates:
            return templates[file_type]
        else:
            return f"Template for '{file_type}' not found. Available templates: {', '.join(templates.keys())}"
    
    @sqlite_agent.tool
    async def validate_file_path(ctx: RunContext[SQLiteConfigInput], file_path: str) -> str:
        """
        Validate a file path and suggest corrections if needed.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Validation result with suggestions if needed
        """
        # Ensure path starts with /
        if not file_path.startswith('/'):
            file_path = '/' + file_path
        
        # Check against path templates if available
        if ctx.deps.path_templates:
            templates = ctx.deps.path_templates
            
            # Check if this is a schema file
            if file_path.endswith('schema.sql') and file_path != templates['schema']:
                return f"Warning: Schema file should be at {templates['schema']} instead of {file_path}"
            
            # Check if this is a db connection file
            if file_path.endswith('db.js') and '/lib/' in file_path and file_path != templates['db_connection']:
                return f"Warning: Database connection file should be at {templates['db_connection']} instead of {file_path}"
            
            # Check if this is a queries file
            if ('queries' in file_path or 'db-queries' in file_path) and file_path != templates['db_queries']:
                return f"Warning: Database queries file should be at {templates['db_queries']} instead of {file_path}"
            
            # Check if this is an API route
            if '/api/' in file_path and not file_path.startswith(templates['api_base']):
                return f"Warning: API routes should be under {templates['api_base']} directory"
        
        # Path looks good
        return f"Path {file_path} is valid"
    
    return sqlite_agent
    