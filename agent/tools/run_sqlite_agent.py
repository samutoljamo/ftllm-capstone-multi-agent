from pydantic import BaseModel
from pydantic_ai import RunContext, Tool, Agent
from pydantic_ai.usage import UsageLimits, Usage
from agents.context import SQLiteConfigInput, SQLiteConfigOutput
from typing import Optional, List, Dict, Any
from pydantic_ai.models.openai import OpenAIModel
import os
import json

async def run_sqlite_agent_and_implement(
    sqlite_agent: Agent,
    app_description: str,
    existing_files: Optional[List[str]] = None,
    file_contents: Optional[Dict[str, str]] = None,
    include_auth: bool = True,
    include_session: bool = True,
    database_name: str = "app.db",
    project_path: Optional[str] = None,
    usage_limits: Optional[UsageLimits] = None,
    context: Optional[RunContext] = None,
    ai_model: Optional[OpenAIModel] = None,
    deps: Optional[BaseModel] = None

) -> SQLiteConfigOutput:
    """
    Runs the SQLite agent and implements its file outputs in the project.
    
    Args:
        sqlite_agent: The SQLite database agent
        app_description: Description of the application
        existing_files: List of existing file paths
        file_contents: Contents of existing files
        include_auth: Whether to include authentication
        include_session: Whether to include session management
        database_name: Name of the database file
        project_path: Base path of the project for file operations
        usage_limits: Usage limits for the agent
        context: RunContext to use for the agent (optional)
        
    Returns:
        SQLiteConfigOutput with results
    """
    
    print("Running SQLite agent and implementing files")
    if not project_path:
        print("Project path not set. Call set_project_path first.")
        return SQLiteConfigOutput(
            success=False,
            message="Project path not set. Call set_project_path first.",
            created_files=[]
        )
    
    print("app description for sqlite agent", app_description)


    # Configure agent input
    agent_input = SQLiteConfigInput(
        app_description=app_description,
        existing_files=existing_files,
        file_contents=file_contents,
        include_auth=include_auth,
        include_session=include_session,
        database_name=database_name,
        path_templates={
            "schema": "/db/schema.sql",
            "db_connection": "/lib/db.js",
            "db_queries": "/lib/db-queries.js",
            "api_base": "/pages/api"
        }
    )
    print("agent input created")
    
    path_templates={
            "schema": "/db/schema.sql",
            "db_connection": "/lib/db.js",
            "db_queries": "/lib/db-queries.js",
            "api_base": "/pages/api"
        }

    input_data = {
        "project_description": app_description,
        "project_path": project_path,
        "existing_files": existing_files,
        "file_contents": file_contents,
        "include_auth": include_auth,
        "include_session": include_session,
        "database_name": database_name,
        "path_templates": json.dumps(path_templates)
    }
    
    # Run the SQLite agent to design the database
    try:
        print("Running SQLite agent")
        

        result = await sqlite_agent.run(
            json.dumps(input_data),
            usage_limits=usage_limits or UsageLimits(request_limit=10, total_tokens_limit=100000),
            model=ai_model
        )
        
        print("SQLite agent run completed")
        
        if not result.success:
            print(f"SQLite agent failed: {result.error_message}")
            return SQLiteConfigOutput(
                success=False,
                message=f"SQLite agent failed: {result.error_message}",
                created_files=[]
            )
            
        return result
        
    except Exception as e:
        print("SQLite agent execution failed")
        print(e)
        return SQLiteConfigOutput(
            success=False,
            message=f"SQLite agent execution failed: {str(e)}",
            created_files=[]
        )