from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
import os
from typing import Optional


class ReadFileInput(BaseModel):
    file_path: str  # Path relative to project root or predefined directories

class ReadFileOutput(BaseModel):
    content: str
    error: Optional[str] = None

def read_file_content (ctx: RunContext, input: ReadFileInput) -> ReadFileOutput:
    # Handle paths that might come in different formats
    path = input.file_path
    if path.startswith("/"):
        path = path[1:]
    
    # Determine if this is a special path that needs mapping
    if path.startswith("api/"):
        actual_path = os.path.join(ctx.deps.project_path, "pages", path)
    elif path.startswith("db/"):
        actual_path = os.path.join(ctx.deps.project_path, path)
    else:
        return ReadFileOutput(
            content="", 
            error=f"Access denied: Database agent can only read from api/ or db/ paths"
        )
    
    try:
        with open(actual_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ReadFileOutput(content=content)
    except FileNotFoundError:
        return ReadFileOutput(content="")

read_file_content = Tool(read_file_content)