import subprocess
import os
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal, Any
import json
import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits, Usage
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv; load_dotenv()

# Import our utility functions
from utils.nextjs_project import create_base_nextjs_project
from utils.cypress_runner import run_cypress_tests

# Import agents
from agents import code_generation, cypress_tests, feedback
from agents.context import CodeGenerationDeps, FeedbackOutput


# =======================
# Define AI Model and Usage Limits
# =======================x

# Define a common usage limit for all agents
DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=100, total_tokens_limit=1000000)

# Initialize the model (adjust as needed for your environment)
ai_model = OpenAIModel(
    model_name='gpt-4o-mini'
)

# =======================
# Simplified development flow with direct agent invocation using the tools
# =======================

async def generate_code_with_tools(project_description: str, project_path: str, deps: CodeGenerationDeps, feedback: Optional[str] = None) -> None:
    """Generate code for the Next.js application using the code generation agent with tools"""
    print("Generating code...")
    
    # Prepare input for the code generation agent
    input_data = {
        "project_description": project_description,
        "feedback": feedback,
        "project_path": project_path
    }
    
    # Call code generation agent - instead of returning files, it will use tools to write them
    await code_generation.run(
        json.dumps(input_data),
        usage_limits=DEFAULT_USAGE_LIMITS,
        model=ai_model,
        deps=deps
    )
    print("code generation agent " )
    print(code_generation)
    
    print(f"Code generation completed, files written to project")

async def generate_cypress_tests_with_tools(project_path: str, deps: CodeGenerationDeps) -> None:
    """Generate Cypress tests for the application using the cypress tests agent with tools"""
    print("Generating Cypress tests...")
    
    # Call cypress tests agent - it will use tools to read pages and write tests
    await cypress_tests.run(
        json.dumps({
            "action": "generate_tests",
            "project_path": project_path
        }),
        usage_limits=DEFAULT_USAGE_LIMITS,
        model=ai_model,
        deps=deps
    )
    
    print("Cypress tests generation completed")

async def get_feedback(test_output: str, test_errors: List[str], server_output: Dict[str, str], deps: CodeGenerationDeps) -> FeedbackOutput:
    """Get feedback based on test results"""
    print("Getting feedback on test results...")
    
    # Prepare input for the feedback agent
    input_data = {
        "test_output": test_output,
        "test_errors": test_errors,
        "server_output": server_output
    }
    
    # Call feedback agent
    result = await feedback.run(
        json.dumps(input_data),
        usage_limits=DEFAULT_USAGE_LIMITS,
        model=ai_model,
        deps=deps
    )
    
    return result.data

async def full_development_flow(project_description: str, max_iterations: int = 5):
    """
    Orchestrates the development process using direct sequential agent invocation with tools.
    
    Args:
        project_description: Description of the project to build
        max_iterations: Maximum number of development iterations
    
    Returns:
        Dictionary with development results
    """
    print("Starting development process...")
    
    # Step 1: Create base project structure
    project_path = os.path.join(os.getcwd(), "nextjs-project")
    create_base_nextjs_project(project_path)
    print(f"Created base Next.js project at {project_path}")
    print(project_path)
    
    # Create a usage tracker for token usage
    usage = Usage()

    
    # Store development artifacts
    feedback_result = None
    
    # Main development loop
    for iteration in range(1, max_iterations + 1):
        deps = CodeGenerationDeps(project_path=project_path, project_description=project_description, ai_model_name=ai_model.model_name, feedback_message=feedback_result.feedback_message if feedback_result else None)
        print(f"\n--- Iteration {iteration}/{max_iterations} ---")
        
        # Step 2: Generate or update code based on feedback
        await generate_code_with_tools(
            project_description,
            project_path,
            deps,
            feedback_result.feedback_message if feedback_result else None
        )
        print(f"Generated code in iteration {iteration}")
        
        # Step 3: Generate Cypress tests
        await generate_cypress_tests_with_tools(project_path, deps)
        print("Generated Cypress tests")
        
        # Step 4: Run tests with enhanced functionality that:
        # - Installs npm packages
        # - Starts the Next.js server
        # - Runs the Cypress tests
        # - Stops the server
        test_result = run_cypress_tests(project_path)
        print(f"Tests ran with success={test_result['success']}")
        
        # If tests pass, we're done
        if test_result['success']:
            print("Tests passed successfully!")
            break
        
        # If tests fail, get feedback for next iteration
        feedback_result = await get_feedback(
            test_result['output'], 
            test_result['errors'], 
            test_result.get('server_output', {}),  # Pass server output to feedback agent
            deps
        )
        print(f"Feedback: {feedback_result.feedback_message}")
        
        # If this was the last iteration, we're done even if tests failed
        if iteration == max_iterations:
            print(f"Reached maximum iterations ({max_iterations})")
    
    # Return development results
    return {
        "final_project_path": project_path,
        "tests_passed": test_result['success'] if 'test_result' in locals() else False,
        "iterations_completed": iteration
    }

# Example usage
if __name__ == "__main__":
    # Example project description
    project_description = """
Create a simple Next.js application for a personal recipe collection. 
The application should display a grid of recipe cards, each showing an image, title, preparation time, and difficulty level.
Users should be able to click on a recipe card to view the full details including ingredients, instructions, and serving size.
Implement sorting options to filter recipes by preparation time, difficulty, or newest additions.
The application should feature a responsive, modern design using Tailwind CSS with an appealing color scheme suitable for a food-related website.
    """
    
    # Run the development process with direct agent invocation using tools
    result = asyncio.run(full_development_flow(project_description))
    
    print(f"Development completed after {result['iterations_completed']} iterations")
    print(f"Tests passed: {result['tests_passed']}")
    print(f"Next.js project created at: {result['final_project_path']}")
    print("\nTo run the application:")
    print(f"cd {result['final_project_path']}")
    print("npm install")
    print("npm run dev")
