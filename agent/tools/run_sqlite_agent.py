from pydantic import BaseModel
from pydantic_ai import RunContext, Tool, Agent
from pydantic_ai.usage import UsageLimits
from agents.context import SQLiteConfigOutput, SQLiteConfigInput
from typing import Optional, Dict, Any
from pydantic_ai.models.openai import OpenAIModel
import json

async def run_sqlite_agent_and_implement(
    sqlite_agent: Agent,
    app_description: str,
    include_auth: bool = True,
    include_session: bool = True,
    database_name: str = "app.db",
    project_path: Optional[str] = None,
    usage_limits: Optional[UsageLimits] = None,
    ai_model: Optional[OpenAIModel] = None,
    deps: Optional[SQLiteConfigInput] = None
) -> SQLiteConfigOutput:
    """
    Runs the SQLite agent and implements its file outputs in the project.
    
    Args:
        sqlite_agent: The SQLite database agent
        app_description: Description of the application
        include_auth: Whether to include authentication
        include_session: Whether to include session management
        database_name: Name of the database file
        project_path: Base path of the project for file operations
        usage_limits: Usage limits for the agent
        ai_model: AI model to use
        
    Returns:
        SQLiteConfigOutput with results
    """
    
    print("Running SQLite agent and implementing files")
    if not project_path:
        print("Project path not set")
        return SQLiteConfigOutput(
            success=False,
            message="Project path not set",
            created_files=[]
        )
    
    # Updated path templates to match your new structure
    path_templates = {
        "schema": "/db/schema.sql",
        "db_connection": "/db/connection.js",
        "db_queries": "/db/queries.js",
        "api_base": "/pages/api"
    }

    # Configure the input data for the agent
    input_data = {
        "project_description": app_description,
        "project_path": project_path,
        "include_auth": include_auth,
        "include_session": include_session,
        "database_name": database_name,
        "path_templates": path_templates
    }
    
    # Run the SQLite agent to design the database
    try:
        print("Running SQLite agent")
        print(f"- Project path: {project_path}")
        print(f"- Database name: {database_name}")
        
        # Set default usage limits if none provided
        if not usage_limits:
            usage_limits = UsageLimits(request_limit=10, total_tokens_limit=100000)
        
        # Run the agent
        result = await sqlite_agent.run(
            json.dumps(input_data),
            usage_limits=usage_limits,
            model=ai_model,
            deps=deps
        )
        
        print("SQLite agent run completed")
        
        # Check result type and handle accordingly
        if hasattr(result, 'data') and result.data is not None:
            # The pydantic-ai agent returns a wrapper object with a data attribute
            return result.data
        elif isinstance(result, SQLiteConfigOutput):
            # The agent directly returned a SQLiteConfigOutput
            return result
        elif hasattr(result, 'error_message') and result.error_message:
            # The agent returned an error
            print(f"SQLite agent failed: {result.error_message}")
            return SQLiteConfigOutput(
                success=False,
                message=f"SQLite agent failed: {result.error_message}",
                created_files=[]
            )
        else:
            # Fallback case for unknown result type
            error_msg = "Unknown result format from SQLite agent"
            print(error_msg)
            return SQLiteConfigOutput(
                success=False,
                message=error_msg,
                created_files=[]
            )
        
    except Exception as e:
        import traceback
        print("SQLite agent execution failed with exception:")
        print(traceback.format_exc())
        return SQLiteConfigOutput(
            success=False,
            message=f"SQLite agent execution failed: {str(e)}",
            created_files=[]
        )