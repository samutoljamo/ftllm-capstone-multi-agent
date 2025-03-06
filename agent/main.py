from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits
from typing import Dict, List, Any, Optional
import json
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel

from dotenv import load_dotenv; load_dotenv()

# Define a common usage limit for all agents
DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=10, total_tokens_limit=5000)

ollama_model = OpenAIModel(
    model_name='llama3.2', provider=OpenAIProvider(base_url='http://localhost:11434/v1')
)

# Requirements Analysis Agent
requirements_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a requirements analysis expert. Given a user request, you generate detailed '
        'software specifications including functional requirements, non-functional requirements, '
        'and acceptance criteria. Be thorough yet concise.'
    ),
#    result_type=Dict[str, Any]
)

# Code Generation Agent
code_generation_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a code generation expert. Given software specifications, you write clean, '
        'efficient code that meets those requirements. Your code is well-structured, properly '
        'commented, and follows best practices for the chosen programming language.'
    ),
 #   result_type=Dict[str, str]
)



# Project Coordination Agent
coordinator_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are the lead software architect coordinating the development process. You delegate tasks '
        'to specialized agents, synthesize their outputs, and ensure the final product meets all requirements. '
        'You make final decisions about architecture and implementation approaches.'
    )
)

review_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a code review expert. You analyze code for bugs, readability, efficiency, '
        'and adherence to best practices. You provide specific, actionable feedback to improve code quality.'
    ),
    result_type=bool
)


# Tools for the coordinator agent
@coordinator_agent.tool
async def analyze_requirements(ctx: RunContext[None], user_request: str) -> Dict[str, Any]:
    """
    Analyze user requirements and generate detailed software specifications.
    """
    result = await requirements_agent.run(
        f"Analyze the following user request and generate detailed software specifications:\n\n{user_request}",
        usage=ctx.usage
    )
    return result.data


@coordinator_agent.tool
async def generate_code(ctx: RunContext[None], specifications: Dict[str, Any], language: str) -> Dict[str, str]:
    """
    Generate code based on software specifications.
    """
    specs_str = json.dumps(specifications, indent=2)
    result = await code_generation_agent.run(
        f"Generate {language} code based on these specifications:\n\n{specs_str}",
        usage=ctx.usage
    )
    return result.data


@coordinator_agent.tool
async def review_code(ctx: RunContext[None], code: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Review generated code and provide feedback.
    """
    code_str = json.dumps(code, indent=2)
    result = await review_agent.run(
        f"Review the following code and provide detailed feedback:\n\n{code_str}",
        usage=ctx.usage
    )
    return result.data




async def develop_software(user_request: str, language: str = "Python") -> Dict[str, Any]:
    """
    Main function to coordinate the software development process using multiple agents.
    
    Args:
        user_request: The user's software requirements or feature request
        language: The programming language to use for implementation
        
    Returns:
        A dictionary containing the full software development artifacts
    """
    
    while True:

        # Analyze user requirements
        requirements_result = await 

        result = await coordinator_agent.run(
            f"Develop software based on this request using {language}: {user_request}",
            usage_limits=DEFAULT_USAGE_LIMITS
        )


        # review all requirements

    return {
        "summary": result.data,
        "usage_stats": result.usage()
    }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Example user request
    user_request = """
    Create a web API for a task management system with the following features:
    1. Users can create, read, update, and delete tasks
    2. Tasks have a title, description, due date, priority, and status
    3. Users can filter and sort tasks by various criteria
    4. The system should validate inputs and handle errors gracefully
    """
    
    # Run the development process
    result = asyncio.run(develop_software(user_request))
    
    # Print the result
    print("Development Summary:")
    print(result["summary"])
    print("\nUsage Statistics:")
    print(result["usage_stats"])