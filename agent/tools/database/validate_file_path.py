from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from agents.context import SQLiteConfigInput
from typing import Dict, Any

async def validate_file_path(ctx: RunContext, file_path: str) -> str:
    print(f"Validating file path: {file_path}")
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


validate_file_path = Tool(validate_file_path)