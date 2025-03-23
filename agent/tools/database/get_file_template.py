from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from agents.context import SQLiteConfigInput
from typing import Dict, Any



async def get_file_template(ctx: RunContext, file_type: str) -> str:
        print(f"Getting template for: {file_type}")
        
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
        

get_file_template = Tool(get_file_template)