from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Dict, Any
import os


async def write_file(ctx: RunContext, file_path: str, content: str) -> str:
    """
    Write content to a file in the project.
    
    Args:
        file_path: Path where the file should be written
        content: Content to write to the file
        
    Returns:
        Success message or error
    """
    print(f"Writing file: {file_path}")
    
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # Actually write the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"File written successfully: {file_path}")
        return f"File {file_path} created successfully"
    except Exception as e:
        print(f"Failed to write file: {str(e)}")
        return f"Error writing file: {str(e)}"
        

write_file = Tool(write_file)