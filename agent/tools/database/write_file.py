from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Dict, Any
import os

class WriteFileInput(BaseModel):
    file_path: str
    content: str

class WriteFileOutput(BaseModel):
    success: bool
    message: str

def _write_file(ctx: RunContext, input: WriteFileInput) -> WriteFileOutput:
    path = input.file_path
    if path.startswith("/"):
        path = path[1:]
    
    # Check if the path is within allowed directories
    if path.startswith("api/") or path.startswith("pages/api/"):
        actual_path = os.path.join(ctx.deps.project_path, "pages", path.replace("pages/", ""))
    elif path.startswith("db/"):
        actual_path = os.path.join(ctx.deps.project_path, path)
    else:
        return WriteFileOutput(
            success=False, 
            message=f"Access denied: Database agent can only write to api/ or db/ paths"
        )
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(actual_path), exist_ok=True)
        
        # Write the file
        with open(actual_path, "w", encoding="utf-8") as f:
            f.write(input.content)
        
        return WriteFileOutput(success=True, message=f"File {input.file_path} written successfully")
    except Exception as e:
        return WriteFileOutput(success=False, message=f"Error writing file: {str(e)}")

write_file = Tool(_write_file)