from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
import os
from typing import Dict, Any
from agents.sqlite_agent import create_sqlite_agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.usage import UsageLimits
import json


async def generate_sqlite_database(
    ctx: RunContext[Dict[str, Any]], 
) -> str:
    """
    Generate a SQLite database for the Next.js application.
    
    Args:
        database_name: Name of the SQLite database file (default: "app.db")
        
    Returns:
        A message describing the result of the database generation
    """
    print("Generating SQLite database...")
    
    # Get project path from context
    project_path = getattr(ctx.deps, 'project_path', None)
    if not project_path:
        return "Failed to generate SQLite database: Project path not available in context"
    
    project_description = getattr(ctx.deps, 'project_description', None)
    if not project_description:
        return "Failed to generate SQLite database: Project description not available in context"
    
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
    
    
    # Set default usage limits if none provided

    usage_limits = UsageLimits(request_limit=10, total_tokens_limit=100000)

    
    # Configure the input data for the agent
    input_data = {
        "project_description": project_description,
        "project_path": project_path
    }

    print("Running SQLite agent")
    print(f"- Project path: {project_path}")

    # Run the agent
    result = await sqlite_agent.run(
        json.dumps(input_data),
        usage_limits=usage_limits,
        model=ai_model,
        deps=ctx.deps
    )
    
    print("SQLite agent run completed")
    print(f"SQLite agent result: {result}")


    if result.data.success:
        files_created = "\n- " + "\n- ".join(result.data.created_files)
        return f"SQLite database generated successfully. Created files: {files_created}"
    else:
        return f"Failed to generate SQLite database: {result.data.message}"


# Create the Tool instance for this function
generate_sqlite_database_tool = Tool(generate_sqlite_database)
