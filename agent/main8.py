from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits, Usage
from typing import Dict, List, Any, Optional, TypedDict, Literal, Union
import asyncio
import json
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv; load_dotenv()

# Define typed results for better type safety and consistency
class RequirementsResult(BaseModel):
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    acceptance_criteria: List[str]
    architecture_recommendations: List[str]
    data_model: Dict[str, Any]

class CodeFile(BaseModel):
    filename: str
    content: str
    language: str
    purpose: str

class CodeGenerationResult(BaseModel):
    files: List[CodeFile]
    setup_instructions: str
    dependencies: List[str]

class CodeReviewIssue(BaseModel):
    severity: Literal["critical", "major", "minor", "suggestion"]
    file: str
    line: Optional[int]
    description: str
    recommendation: str

class TestCase(BaseModel):
    name: str
    test_type: Literal["unit", "integration", "e2e", "performance", "security"]
    description: str
    input: Dict[str, Any]
    expected_output: Any
    setup: Optional[str]

class TestingResult(BaseModel):
    test_cases: List[TestCase]
    test_coverage: Dict[str, float]
    testing_strategy: str

class SecurityVulnerability(BaseModel):
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: str
    description: str
    affected_files: List[str]
    recommendation: str
    reference: Optional[str]

class PerformanceIssue(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    issue_type: str
    description: str
    affected_components: List[str]
    recommendation: str
    estimated_impact: str

class DevelopmentSummary(BaseModel):
    key_features: List[str]
    architecture: str
    improvements: List[str]
    future_work: List[str]

# Define a common usage limit for all agents
DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=100, total_tokens_limit=1000000)

# Initialize the model (adjust as needed for your environment)
deepseek_model = OpenAIModel(
    model_name='deepseek-chat', 
    provider=OpenAIProvider(base_url='https://api.deepseek.com')
)

# Dependency type for sharing context between agents
class SDLCContext:
    """Shared context between software development lifecycle agents"""
    
    def __init__(self, project_description: str, language: str):
        self.project_description = project_description
        self.language = language
        self.requirements: Optional[RequirementsResult] = None
        self.code: Optional[CodeGenerationResult] = None
        self.review_issues: List[CodeReviewIssue] = []
        self.test_cases: Optional[TestingResult] = None
        self.security_issues: List[SecurityVulnerability] = []
        self.performance_issues: List[PerformanceIssue] = []
        self.iteration: int = 1
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to a dictionary for serialization"""
        return {
            "project_description": self.project_description,
            "language": self.language,
            "requirements": self.requirements.model_dump() if self.requirements else None,
            "code": self.code.model_dump() if self.code else None,
            "review_issues": [issue.model_dump() for issue in self.review_issues],
            "test_cases": self.test_cases.model_dump() if self.test_cases else None,
            "security_issues": [issue.model_dump() for issue in self.security_issues],
            "performance_issues": [issue.model_dump() for issue in self.performance_issues],
            "iteration": self.iteration,
            "timestamp": self.timestamp
        }

# Requirements Analysis Agent
requirements_agent = Agent(
    deepseek_model,
    deps_type=str,  # Takes the project description as input
    result_type=RequirementsResult,
    system_prompt=(
        "You are a requirements analysis expert. Given a user request, you generate detailed "
        "software specifications including functional requirements, non-functional requirements, "
        "acceptance criteria, architecture recommendations, and a data model."
    )
)

# Code Generation Agent
code_generation_agent = Agent(
    deepseek_model,
    deps_type=Dict[str, Any],  # Takes requirements and feedback
    result_type=CodeGenerationResult,
    system_prompt=(
        "You are a code generation expert. Given software specifications, you write clean, "
        "efficient code that meets those requirements. Your code is well-structured, properly "
        "commented, and follows best practices for the chosen programming language."
    )
)

# Code Review Agent
code_review_agent = Agent(
    deepseek_model,
    deps_type=Dict[str, Any],  # Takes code and requirements
    result_type=List[CodeReviewIssue],
    system_prompt=(
        "You are a code review expert. You analyze code for bugs, readability, efficiency, "
        "and adherence to best practices. You provide specific, actionable feedback to improve code quality."
    )
)

# Testing Agent
testing_agent = Agent(
    deepseek_model,
    deps_type=Dict[str, Any],  # Takes code and requirements
    result_type=TestingResult,
    system_prompt=(
        "You are a testing expert. You generate comprehensive test cases based on requirements "
        "and implementation details. You emphasize edge cases, security tests, and performance tests."
    )
)

# Security Agent
security_agent = Agent(
    deepseek_model,
    deps_type=Dict[str, Any],  # Takes code and requirements
    result_type=List[SecurityVulnerability],
    system_prompt=(
        "You are a security expert. You identify potential security vulnerabilities in code "
        "and provide recommendations to address them. You focus on OWASP Top 10 and other "
        "common security concerns."
    )
)

# Performance Optimization Agent
optimization_agent = Agent(
    deepseek_model,
    deps_type=Dict[str, Any],  # Takes code and requirements
    result_type=List[PerformanceIssue],
    system_prompt=(
        "You are a performance optimization expert. You analyze code for inefficiencies "
        "and suggest improvements to enhance speed, reduce resource usage, and improve scalability."
    )
)

# Project Coordinator Agent - Main orchestrator
coordinator_agent = Agent(
    deepseek_model,
    deps_type=SDLCContext,
    result_type=str,
    system_prompt=(
        "You are the lead software architect and project manager coordinating an AI-driven software "
        "development process. Your role is to make strategic decisions about what steps should be taken "
        "next based on the current state of development.\n\n"
        
        "Your responsibilities include:\n"
        "1. Analyzing the current development context to determine the most valuable next step\n"
        "2. Making informed decisions about when to perform requirements analysis, code generation, "
        "testing, security checks, and other development activities\n"
        "3. Determining when issues need to be fixed before proceeding to the next steps\n"
        "4. Deciding when the development process is complete\n"
        "5. Providing clear reasoning for each decision you make\n\n"
        
        "You have access to specialized tools for each phase of development. Use these tools as needed.\n"
        "Call these tools directly rather than trying to perform their functions yourself.\n\n"
        
        "Your goal is to deliver high-quality software that meets all requirements through an "
        "efficient development process. You'll update the project state after each decision."

        "Code generation and code improvement tools generate the whole codebase, including setup instructions and dependencies at once."
        "Calling them multiples times will generate new codebases, not incremental changes."

        "After you generate code, review it for issues with your tools and if there are any, make improvements."

        "You may ask questions to the user to clarify requirements or to the tools to get more information."

        "Reviewing tools will always find issues, do not continue forever but determine when to stop."
    )
)

# Development Summary Agent
summary_agent = Agent(
    deepseek_model,
    deps_type=Dict[str, Any],  # Takes all artifacts
    result_type=DevelopmentSummary,
    system_prompt=(
        "You are a technical documentation expert. You review the entire software development process "
        "and create a comprehensive summary highlighting key features, architecture decisions, "
        "improvements made during development, and suggestions for future work."
    )
)
"""
@coordinator_agent.tool
async def ask_for_context(ctx: RunContext[None], question: str) -> str:
    # Ask for the user's software requirements to start the development process.
    answer = input(question + " ")
    return answer

"""


# Tool implementations for the coordinator agent
@coordinator_agent.tool
async def analyze_requirements(ctx: RunContext[SDLCContext]) -> RequirementsResult:
    """
    Analyze the user requirements and generate detailed software specifications.
    This should be the first tool called in the development process.
    """
    # Use the requirements agent by delegating work to it
    # This shows agent delegation pattern from the documentation
    result = await requirements_agent.run(
        ctx.deps.project_description,
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Store the result in the shared context
    ctx.deps.requirements = result.data

    print("Analyzed requirements and generated specifications", result.data)
    
    # Return the result directly
    return result.data

@coordinator_agent.tool
async def generate_code(ctx: RunContext[SDLCContext]) -> str:
    """
    Generate code based on the requirements and any feedback from previous reviews.
    Requires requirements to be analyzed first.
    """
    if not ctx.deps.requirements:
        raise ValueError("Requirements must be analyzed before generating code")
    
    # Prepare input for the code generation agent
    input_data = {
        "specifications": ctx.deps.requirements.model_dump(),
        "language": ctx.deps.language,
        "review_feedback": [issue.model_dump() for issue in ctx.deps.review_issues] if ctx.deps.review_issues else []
    }
    
    # Call code generation agent with the prepared input
    result = await code_generation_agent.run(
        json.dumps(input_data),
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Store the result in the shared context
    ctx.deps.code = result.data
    print(f"Generated {len(result.data.files)} files of code", result.data)
    
    return f"Generated {len(result.data.files)} files of code"

@coordinator_agent.tool
async def review_code(ctx: RunContext[SDLCContext]) -> str:
    """
    Review the generated code for issues related to correctness, structure, and best practices.
    Requires code to be generated first.
    """
    if not ctx.deps.code or not ctx.deps.requirements:
        raise ValueError("Both code and requirements must exist before reviewing")
    
    # Prepare input for the code review agent
    input_data = {
        "code": ctx.deps.code.model_dump(),
        "specifications": ctx.deps.requirements.model_dump()
    }
    
    # Call code review agent with the prepared input
    result = await code_review_agent.run(
        json.dumps(input_data),
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Store the result in the shared context
    ctx.deps.review_issues = result.data
    
    print(f"Found {len(result.data)} issues in the code", result.data)
    # Return the result directly
    return f"Found {len(result.data)} issues in the code"

@coordinator_agent.tool
async def create_tests(ctx: RunContext[SDLCContext]) -> str:
    """
    Generate test cases based on the requirements and implementation.
    Requires code to be generated first.
    """
    if not ctx.deps.code or not ctx.deps.requirements:
        raise ValueError("Both code and requirements must exist before creating tests")
    
    # Prepare input for the testing agent
    input_data = {
        "code": ctx.deps.code.model_dump(),
        "specifications": ctx.deps.requirements.model_dump()
    }
    
    # Call testing agent with the prepared input
    result = await testing_agent.run(
        json.dumps(input_data),
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Store the result in the shared context
    ctx.deps.test_cases = result.data
    
    print(f"Generated {len(result.data.test_cases)} test cases", result.data)
    # Return the result directly
    return f"Generated {len(result.data.test_cases)} test cases"

@coordinator_agent.tool
async def check_security(ctx: RunContext[SDLCContext]) -> str:
    """
    Analyze code for security vulnerabilities.
    Requires code to be generated first.
    """
    if not ctx.deps.code or not ctx.deps.requirements:
        raise ValueError("Both code and requirements must exist before security check")
    
    # Prepare input for the security agent
    input_data = {
        "code": ctx.deps.code.model_dump(),
        "specifications": ctx.deps.requirements.model_dump()
    }
    
    # Call security agent with the prepared input
    result = await security_agent.run(
        json.dumps(input_data),
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Store the result in the shared context
    ctx.deps.security_issues = result.data

    print(f"Found {len(result.data)} security issues", result.data)
    
    # Return the result directly
    return f"Found {len(result.data)} security issues"

@coordinator_agent.tool
async def optimize_performance(ctx: RunContext[SDLCContext]) -> str:
    """
    Analyze code for performance inefficiencies.
    Requires code to be generated first.
    """
    if not ctx.deps.code or not ctx.deps.requirements:
        raise ValueError("Both code and requirements must exist before performance optimization")
    
    # Prepare input for the optimization agent
    input_data = {
        "code": ctx.deps.code.model_dump(),
        "specifications": ctx.deps.requirements.model_dump()
    }
    
    # Call optimization agent with the prepared input
    result = await optimization_agent.run(
        json.dumps(input_data),
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Store the result in the shared context
    ctx.deps.performance_issues = result.data
    

    
    print(f"Found {len(result.data)} performance issues", result.data)
    return f"Found {len(result.data)} performance issues"

@coordinator_agent.tool
async def make_improvements(ctx: RunContext[SDLCContext]) -> str:
    """
    Improve code based on review, security, and performance feedback.
    Requires code, review issues, security issues, or performance issues to exist.
    """
    if not ctx.deps.code:
        raise ValueError("Code must exist before making improvements")
    
    # At least one type of issues should exist
    if not (ctx.deps.review_issues or ctx.deps.security_issues or ctx.deps.performance_issues):
        raise ValueError("At least one type of issues must exist before making improvements")
    
    # Prepare input for the code generation agent with all issues
    input_data = {
        "specifications": ctx.deps.requirements.model_dump(),
        "language": ctx.deps.language,
        "original_code": ctx.deps.code.model_dump(),
        "review_issues": [issue.model_dump() for issue in ctx.deps.review_issues] if ctx.deps.review_issues else [],
        "security_issues": [issue.model_dump() for issue in ctx.deps.security_issues] if ctx.deps.security_issues else [],
        "performance_issues": [issue.model_dump() for issue in ctx.deps.performance_issues] if ctx.deps.performance_issues else []
    }
    
    # Call code generation agent with the prepared input
    result = await code_generation_agent.run(
        json.dumps(input_data),
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Store the result and increment iteration counter
    ctx.deps.code = result.data
    ctx.deps.iteration += 1
    
    # Reset issues since they've been addressed
    ctx.deps.review_issues = []
    ctx.deps.security_issues = []
    ctx.deps.performance_issues = []

    print(f"Generated improved code for iteration {ctx.deps.iteration}", result.data)
    return f"Generated improved code for iteration {ctx.deps.iteration}"


@coordinator_agent.tool
async def generate_summary(ctx: RunContext[SDLCContext]) -> DevelopmentSummary:
    """
    Generate a comprehensive summary of the completed development process.
    Should be called once development is considered complete.
    """
    if not ctx.deps.code or not ctx.deps.requirements:
        raise ValueError("Both code and requirements must exist before generating summary")
    
    # Prepare input for the summary agent
    input_data = {
        "project_description": ctx.deps.project_description,
        "language": ctx.deps.language,
        "iteration_count": ctx.deps.iteration,
        "requirements": ctx.deps.requirements.model_dump(),
        "code": ctx.deps.code.model_dump(),
        "tests": ctx.deps.test_cases.model_dump() if ctx.deps.test_cases else None,
        "review_issues": [issue.model_dump() for issue in ctx.deps.review_issues] if ctx.deps.review_issues else [],
        "security_issues": [issue.model_dump() for issue in ctx.deps.security_issues] if ctx.deps.security_issues else [],
        "performance_issues": [issue.model_dump() for issue in ctx.deps.performance_issues] if ctx.deps.performance_issues else []
    }
    
    # Call summary agent with the prepared input
    result = await summary_agent.run(
        json.dumps(input_data),
        usage=ctx.usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Return the result directly
    return result.data

async def develop_software(project_description: str, language: str = "Python") -> SDLCContext:
    """
    Main function that orchestrates the development process using agent delegation.
    
    Args:
        project_description: The user's software requirements or feature request
        language: The programming language to use for implementation
        max_iterations: Maximum number of iterations to prevent infinite loops
        
    Returns:
        A dictionary containing the final software development artifacts
    """
    # Create a shared context for all agents
    sdlc_context = SDLCContext(project_description, language)
    
    # Create a usage tracker to monitor token usage across all agents
    usage = Usage()

    print(f"\n=== Starting software development process ===")

    await coordinator_agent.run(
        f"Develop software based on this request using {language}: {project_description}",
        deps=sdlc_context,
        usage=usage,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    print(f"\n=== Development completed ===")
    print(f"Total token usage: {usage.total_tokens}")
    
    return sdlc_context

# Example usage
if __name__ == "__main__":
    # Example user request
    project_description = """
    Create a web API for a task management system with the following features:
    1. Users can create, read, update, and delete tasks
    2. Tasks have a title, description, due date, priority, and status
    3. Users can filter and sort tasks by various criteria
    4. The system should validate inputs and handle errors gracefully
    """

    project = """
        Generate a simple snake game.
    """
    
    # Run the development process
    result = asyncio.run(develop_software(project_description, "Python"))
    
    # Print the result
    print("\n== DEVELOPMENT COMPLETE ==")
    # Save all context to a file for further analysis
    with open("development_context.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2)