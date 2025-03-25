from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Dict, Any, Optional
import os

class CreateDirectoryInput(BaseModel):
    directory_path: str  # Path to the directory to create

class CreateDirectoryOutput(BaseModel):
    success: bool
    message: str

def _create_directory(ctx: RunContext, input: CreateDirectoryInput) -> CreateDirectoryOutput:
    """
    Create a directory in the database or API structure.
    
    Args:
        directory_path: Path to the directory to create (must be within db/ or pages/api/)
        
    Returns:
        Success message or error
    """
    print(f"Creating directory: {input.directory_path}")
    
    # Normalize path (remove leading slash)
    directory_path = input.directory_path
    if directory_path.startswith('/'):
        directory_path = directory_path[1:]
    
    try:
        # Check if path is valid for database agent
        if directory_path.startswith('db/') or directory_path == 'db':
            # Database directory
            area = "database"
            # Simply join with project path
            full_path = os.path.join(ctx.deps.project_path, directory_path)
        elif directory_path.startswith('pages/api/') or directory_path == 'pages/api':
            # API directory
            area = "API"
            full_path = os.path.join(ctx.deps.project_path, directory_path)
        elif directory_path.startswith('api/'):
            # Convert api/ to pages/api/
            area = "API"
            full_path = os.path.join(ctx.deps.project_path, 'pages', directory_path)
        else:
            return CreateDirectoryOutput(
                success=False,
                message=f"Error: Directory path must start with 'db/', 'pages/api/', or 'api/'"
            )
        
        # Security check to prevent directory traversal
        project_dir = os.path.realpath(ctx.deps.project_path)
        real_path = os.path.realpath(full_path)
        if not real_path.startswith(project_dir):
            error_msg = f"Security error: Attempted to create directory outside project: {directory_path}"
            print(error_msg)
            return CreateDirectoryOutput(success=False, message=error_msg)
        
        # Create the requested directory
        os.makedirs(full_path, exist_ok=True)
        print(f"Directory created: {full_path}")
        return CreateDirectoryOutput(
            success=True,
            message=f"Directory '{directory_path}' created successfully in the {area} structure"
        )
    except Exception as e:
        print(f"Failed to create directory: {str(e)}")
        return CreateDirectoryOutput(success=False, message=f"Error creating directory: {str(e)}")

create_directory = Tool(_create_directory)