from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import List, Dict, Any

async def list_available_files(ctx: RunContext) -> List[str]:
    print("Listing available files...")
    """
    List all available files that can be analyzed.
    
        Returns:
            List of file paths that can be read
        """
    if ctx.deps.existing_files:
        return ctx.deps.existing_files
    return []

list_available_files = Tool(list_available_files)