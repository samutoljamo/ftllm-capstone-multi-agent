from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Dict, Any
import os


async def create_directory(ctx: RunContext, directory_path: str) -> str:
    """
    Create a directory in the project.
    
    Args:
        directory_path: Path to the directory to create
        
    Returns:
        Success message or error
    """

    print(f"Creating directory: {directory_path}")
    
    try:
        # Actually create the directory
        os.makedirs(directory_path, exist_ok=True)
        print(f"Directory created: {directory_path}")
        return f"Directory {directory_path} created successfully"
    except Exception as e:
        print(f"Failed to create directory: {str(e)}")
        return f"Error creating directory: {str(e)}"
        
    

create_directory = Tool(create_directory)