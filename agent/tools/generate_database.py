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
    database_generation_instructions: str = None,
    feedback: str = None
) -> str:
    """
    Generate a SQLite database for the Next.js application.
    
    Args:
        database_generation_instructions: Instructions on how to design or improve the database.
        
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

    usage_limits = UsageLimits(request_limit=100, total_tokens_limit=100000)

    # Configure the input data for the agent
    input_data = {
        "project_description": project_description,
        "project_path": project_path,
        "database_generation_instructions": database_generation_instructions,
        "feedback": feedback,
        "feedback_message": ctx.deps.feedback_message
    }

    print("Running SQLite agent")
    print(f"- Project path: {project_path}")
    print(f"- Database generation instructions: {database_generation_instructions}")
    print(f"- Feedback: {feedback}")
    print(f"- Feedback from deps: {ctx.deps.feedback_message}")
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
        return f"SQLite database generated successfully: \n\n{result.data.api_documentation}"
    else:
        return f"Failed to generate SQLite database: {result.data.message}"


# Create the Tool instance for this function
generate_sqlite_database_tool = Tool(generate_sqlite_database)
