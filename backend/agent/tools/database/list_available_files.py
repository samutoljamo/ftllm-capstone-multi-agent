from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import List, Dict, Any
import os
from ..tool_notifier import tool_notifier

async def list_available_files(ctx: RunContext) -> List[str]:
    print("Listing available database and API files...")
    """
    List all available database and API files that can be analyzed.
    
    Returns:
        List of file paths relevant to the database agent
    """
    print("Listing available files for database agent")
    
    # Scan the relevant directories
    project_path = ctx.deps.project_path
    files = []
    
    # Check database directory
    db_dir = os.path.join(project_path, "db")
    if os.path.exists(db_dir):
        for root, _, filenames in os.walk(db_dir):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                full_path = os.path.join(root, filename)
                # Create a path relative to the project but with "db/" prefix
                relative_path = os.path.relpath(full_path, project_path)
                files.append(relative_path)
    else:
        print("Database directory (db) not found")
    
    # Check API directory
    api_dir = os.path.join(project_path, "pages", "api")
    if os.path.exists(api_dir):
        for root, _, filenames in os.walk(api_dir):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                full_path = os.path.join(root, filename)
                # Create a path relative to the project
                relative_path = os.path.relpath(full_path, project_path)
                files.append(relative_path)
    else:
        print("API directory (pages/api) not found")
    
    print(f"Database agent found {len(files)} files: {files}")
    return files

list_available_files = Tool(tool_notifier(list_available_files))