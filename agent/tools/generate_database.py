from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
import os
from typing import Dict, Any
from agents.sqlite_agent import create_sqlite_agent
from tools.run_sqlite_agent import run_sqlite_agent_and_implement
from pydantic_ai.models.openai import OpenAIModel


async def generate_sqlite_database(
    ctx: RunContext[Dict[str, Any]], 
    include_auth: bool = True,
    include_session: bool = True,
    database_name: str = "app.db",
) -> str:
    """
    Generate a SQLite database for the Next.js application.
    
    Args:
        include_auth: Whether to include authentication features (default: True)
        include_session: Whether to include session management (default: True)
        database_name: Name of the SQLite database file (default: "app.db")
        
    Returns:
        A message describing the result of the database generation
    """
    print("Generating SQLite database...")
    
    # Get project path from context
    project_path = getattr(ctx.deps, 'project_path', None)
    if not project_path:
        return "Failed to generate SQLite database: Project path not available in context"
    
    # Get AI model from context
    ai_model_name = getattr(ctx.deps, 'ai_model_name', None)
    ai_model_obj = getattr(ctx.deps, 'ai_model', None)
    
    if ai_model_obj and hasattr(ai_model_obj, 'model_name'):
        ai_model = ai_model_obj
    elif ai_model_name:
        ai_model = OpenAIModel(model_name=ai_model_name)
    else:
        return "Failed to generate SQLite database: AI model not available in context"
    
    print(f"Using AI model: {ai_model.model_name}")
    
    # Run the SQLite agent
    sqlite_agent = create_sqlite_agent()
    
    result = await run_sqlite_agent_and_implement(
        sqlite_agent=sqlite_agent,
        app_description=ctx.deps.project_description,
        include_auth=include_auth,
        include_session=include_session,
        database_name=database_name,
        project_path=project_path,
        ai_model=ai_model,
        deps=ctx.deps
    )

    if result.success:
        files_created = "\n- " + "\n- ".join(result.created_files)
        return f"SQLite database generated successfully. Created files: {files_created}"
    else:
        return f"Failed to generate SQLite database: {result.message}"


# Create the Tool instance for this function
generate_sqlite_database_tool = Tool(generate_sqlite_database)
