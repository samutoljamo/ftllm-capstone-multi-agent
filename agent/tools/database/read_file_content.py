from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Dict, Any
from agents.context import SQLiteConfigInput


async def read_file_content(ctx: RunContext, file_path: str) -> str:
    print(f"Reading file content: {file_path}")
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


read_file_content = Tool(read_file_content)