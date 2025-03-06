from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits
from typing import Dict, List, Any, Optional, TypedDict, Literal
import json
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv; load_dotenv()

# Define typed results for better type safety and consistency
class RequirementsResult(TypedDict):
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    acceptance_criteria: List[str]
    architecture_recommendations: List[str]
    data_model: Dict[str, Any]

class CodeFile(TypedDict):
    filename: str
    content: str
    language: str
    purpose: str

class CodeGenerationResult(TypedDict):
    files: List[CodeFile]
    setup_instructions: str
    dependencies: List[str]

class CodeReviewIssue(TypedDict):
    severity: Literal["critical", "major", "minor", "suggestion"]
    file: str
    line: Optional[int]
    description: str
    recommendation: str

class TestCase(TypedDict):
    name: str
    type: Literal["unit", "integration", "e2e", "performance", "security"]
    description: str
    input: Dict[str, Any]
    expected_output: Any
    setup: Optional[str]

class TestingResult(TypedDict):
    test_cases: List[TestCase]
    test_coverage: Dict[str, float]
    testing_strategy: str

class SecurityVulnerability(TypedDict):
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: str
    description: str
    affected_files: List[str]
    recommendation: str
    reference: Optional[str]

class PerformanceIssue(TypedDict):
    severity: Literal["critical", "high", "medium", "low"]
    type: str
    description: str
    affected_components: List[str]
    recommendation: str
    estimated_impact: str

# Context for sharing information between agents
class DevelopmentContext:
    def __init__(self):
        self.requirements: Optional[RequirementsResult] = None
        self.code: Optional[CodeGenerationResult] = None
        self.review_issues: List[CodeReviewIssue] = []
        self.test_cases: Optional[TestingResult] = None
        self.security_issues: List[SecurityVulnerability] = []
        self.performance_issues: List[PerformanceIssue] = []
        self.iteration: int = 1
        self.history: List[Dict[str, Any]] = []
    
    def save_state(self):
        """Save the current state to history"""
        self.history.append({
            "iteration": self.iteration,
            "requirements": self.requirements,
            "code": self.code,
            "review_issues": self.review_issues,
            "test_cases": self.test_cases,
            "security_issues": self.security_issues,
            "performance_issues": self.performance_issues
        })
        self.iteration += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for passing to agents"""
        return {
            "iteration": self.iteration,
            "requirements": self.requirements,
            "code_summary": None if not self.code else {
                "files": [f["filename"] for f in self.code["files"]],
                "dependencies": self.code["dependencies"]
            },
            "review_issues_count": len(self.review_issues),
            "security_issues_count": len(self.security_issues),
            "performance_issues_count": len(self.performance_issues),
            "has_tests": self.test_cases is not None
        }

# Define a common usage limit for all agents
DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=10, total_tokens_limit=5000)

# Initialize the model
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
    result_type=RequirementsResult
)

# Code Generation Agent
code_generation_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a code generation expert. Given software specifications, you write clean, '
        'efficient code that meets those requirements. Your code is well-structured, properly '
        'commented, and follows best practices for the chosen programming language.'
    ),
    result_type=CodeGenerationResult
)

# Code Review Agent
code_review_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a code review expert. You analyze code for bugs, readability, efficiency, '
        'and adherence to best practices. You provide specific, actionable feedback to improve code quality.'
    ),
    result_type=List[CodeReviewIssue]
)

# Testing Agent
testing_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a testing expert. You generate comprehensive test cases based on requirements '
        'and implementation details. You emphasize edge cases, security tests, and performance tests.'
    ),
    result_type=TestingResult
)

# Security Agent
security_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a security expert. You identify potential security vulnerabilities in code '
        'and provide recommendations to address them. You focus on OWASP Top 10 and other '
        'common security concerns.'
    ),
    result_type=List[SecurityVulnerability]
)

# Performance Optimization Agent
optimization_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a performance optimization expert. You analyze code for inefficiencies '
        'and suggest improvements to enhance speed, reduce resource usage, and improve scalability.'
    ),
    result_type=List[PerformanceIssue]
)

# Project Coordination Agent
coordinator_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are the lead software architect coordinating the development process. You delegate tasks '
        'to specialized agents, synthesize their outputs, and ensure the final product meets all requirements. '
        'You make final decisions about architecture and implementation approaches. '
        'You decide when to iterate on the development process and when the final product is ready.'
    )
)

# Add retry decorator for resilience
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def run_agent_with_retry(agent, prompt, usage):
    """Run an agent with retry logic for resilience"""
    try:
        result = await agent.run(prompt, usage=usage)
        return result.data
    except Exception as e:
        print(f"Error running agent: {str(e)}")
        raise

# Tools for the coordinator agent
@coordinator_agent.tool
async def analyze_requirements(ctx: RunContext[None], user_request: str, dev_context: Dict[str, Any]) -> RequirementsResult:
    """
    Analyze user requirements and generate detailed software specifications.
    """
    prompt = f"""
    Analyze the following user request and generate detailed software specifications.
    
    User Request:
    {user_request}
    
    Development Context:
    {json.dumps(dev_context, indent=2)}
    
    Return a structured specification document including:
    1. Functional requirements (what the system should do)
    2. Non-functional requirements (performance, security, usability, etc.)
    3. Acceptance criteria (how to verify the requirements are met)
    4. Architecture recommendations
    5. Data model (entities and relationships)
    """
    
    result = await run_agent_with_retry(requirements_agent, prompt, ctx.usage)
    return result


@coordinator_agent.tool
async def generate_code(
    ctx: RunContext[None], 
    specifications: RequirementsResult, 
    language: str,
    dev_context: Dict[str, Any],
    review_feedback: Optional[List[CodeReviewIssue]] = None
) -> CodeGenerationResult:
    """
    Generate code based on software specifications and optional review feedback.
    """
    specs_str = json.dumps(specifications, indent=2)
    feedback_str = "None" if not review_feedback else json.dumps(review_feedback, indent=2)
    
    prompt = f"""
    Generate {language} code based on these specifications:
    
    Specifications:
    {specs_str}
    
    Development Context:
    {json.dumps(dev_context, indent=2)}
    
    Previous Review Feedback (address these issues):
    {feedback_str}
    
    Create a complete implementation that satisfies all requirements.
    Organize your code into appropriate files and modules.
    Include setup instructions and dependencies.
    """
    
    result = await run_agent_with_retry(code_generation_agent, prompt, ctx.usage)
    return result


@coordinator_agent.tool
async def review_code(
    ctx: RunContext[None], 
    code: CodeGenerationResult, 
    specifications: RequirementsResult
) -> List[CodeReviewIssue]:
    """
    Review generated code and provide feedback.
    """
    code_str = json.dumps(code, indent=2)
    specs_str = json.dumps(specifications, indent=2)
    
    prompt = f"""
    Review the following code and provide detailed feedback:
    
    Code:
    {code_str}
    
    Requirements it should satisfy:
    {specs_str}
    
    Identify issues related to:
    1. Correctness (does it meet the requirements?)
    2. Code structure and organization
    3. Readability and maintainability
    4. Best practices for {code['files'][0]['language'] if code['files'] else 'the language'}
    5. Potential bugs or edge cases
    
    For each issue, specify:
    - The severity (critical, major, minor, suggestion)
    - The affected file
    - Line number (if applicable)
    - A clear description of the issue
    - A specific recommendation to fix it
    """
    
    result = await run_agent_with_retry(code_review_agent, prompt, ctx.usage)
    return result


@coordinator_agent.tool
async def create_tests(
    ctx: RunContext[None], 
    specifications: RequirementsResult, 
    code: CodeGenerationResult
) -> TestingResult:
    """
    Generate test cases based on specifications and implementation.
    """
    specs_str = json.dumps(specifications, indent=2)
    code_files = "\n\n".join([f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" for f in code['files']])
    
    prompt = f"""
    Create comprehensive test cases based on these specifications and implementation:
    
    Specifications:
    {specs_str}
    
    Code Implementation:
    {code_files}
    
    Generate:
    1. Unit tests for individual components
    2. Integration tests for component interactions
    3. End-to-end tests for user workflows
    4. Performance tests for non-functional requirements
    5. Security tests for potential vulnerabilities
    
    For each test, specify:
    - Test name
    - Test type
    - Description
    - Input values
    - Expected output
    - Setup instructions (if needed)
    
    Also include an overall testing strategy and expected test coverage.
    """
    
    result = await run_agent_with_retry(testing_agent, prompt, ctx.usage)
    return result


@coordinator_agent.tool
async def check_security(
    ctx: RunContext[None], 
    code: CodeGenerationResult, 
    specifications: RequirementsResult
) -> List[SecurityVulnerability]:
    """
    Analyze code for security vulnerabilities.
    """
    code_files = "\n\n".join([f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" for f in code['files']])
    specs_str = json.dumps(specifications, indent=2)
    
    prompt = f"""
    Analyze this code for security vulnerabilities and provide recommendations:
    
    Code:
    {code_files}
    
    Requirements:
    {specs_str}
    
    Focus on:
    1. OWASP Top 10 vulnerabilities
    2. Input validation issues
    3. Authentication and authorization flaws
    4. Data protection concerns
    5. Security misconfigurations
    
    For each vulnerability, specify:
    - Severity (critical, high, medium, low, info)
    - Category (e.g., injection, XSS, CSRF)
    - Description
    - Affected files
    - Specific recommendation to fix it
    - Reference (if applicable)
    """
    
    result = await run_agent_with_retry(security_agent, prompt, ctx.usage)
    return result


@coordinator_agent.tool
async def optimize_performance(
    ctx: RunContext[None], 
    code: CodeGenerationResult, 
    specifications: RequirementsResult
) -> List[PerformanceIssue]:
    """
    Analyze code for performance inefficiencies and suggest optimizations.
    """
    code_files = "\n\n".join([f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" for f in code['files']])
    specs_str = json.dumps(specifications, indent=2)
    
    prompt = f"""
    Analyze this code for performance inefficiencies and suggest optimizations:
    
    Code:
    {code_files}
    
    Requirements:
    {specs_str}
    
    Focus on:
    1. Algorithmic efficiency
    2. Resource usage (memory, CPU)
    3. Database query optimization
    4. Network efficiency
    5. Scalability concerns
    
    For each issue, specify:
    - Severity (critical, high, medium, low)
    - Type of issue
    - Description
    - Affected components
    - Specific recommendation to improve performance
    - Estimated impact of the optimization
    """
    
    result = await run_agent_with_retry(optimization_agent, prompt, ctx.usage)
    return result


@coordinator_agent.tool
async def make_improvements(
    ctx: RunContext[None],
    code: CodeGenerationResult,
    issues: Dict[str, Any]
) -> CodeGenerationResult:
    """
    Improve code based on review, security, and performance feedback.
    """
    code_str = json.dumps(code, indent=2)
    issues_str = json.dumps(issues, indent=2)
    
    prompt = f"""
    Update the following code to address the identified issues:
    
    Original Code:
    {code_str}
    
    Issues to Address:
    {issues_str}
    
    Make all necessary changes to fix the issues while maintaining the original functionality.
    Return the complete updated codebase, not just the changes.
    """
    
    result = await run_agent_with_retry(code_generation_agent, prompt, ctx.usage)
    return result


async def develop_software(user_request: str, language: str = "Python", iterations: int = 2) -> Dict[str, Any]:
    """
    Main function to coordinate the software development process using multiple agents.
    
    Args:
        user_request: The user's software requirements or feature request
        language: The programming language to use for implementation
        iterations: Maximum number of improvement iterations
        
    Returns:
        A dictionary containing the full software development artifacts
    """
    dev_context = DevelopmentContext()
    
    # Initial coordination prompt
    initial_prompt = f"""
    Develop software based on this request using {language}:
    
    {user_request}
    
    You'll coordinate a team of specialized AI agents to complete this task.
    Follow this workflow:
    
    1. Analyze requirements
    2. Generate initial code
    3. Review code for issues
    4. Create tests
    5. Check for security vulnerabilities
    6. Identify performance optimizations
    7. Make improvements based on feedback
    8. Repeat steps 3-7 if necessary
    
    Your goal is to produce high-quality software that meets all requirements.
    """
    
    # Start the development process
    coordinator_result = await coordinator_agent.run(
        initial_prompt,
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    # Extract the final artifacts
    return {
        "requirements": dev_context.requirements,
        "code": dev_context.code,
        "tests": dev_context.test_cases,
        "review_issues": dev_context.review_issues,
        "security_issues": dev_context.security_issues,
        "performance_issues": dev_context.performance_issues,
        "development_history": dev_context.history,
        "coordinator_summary": coordinator_result.data,
        "usage_stats": coordinator_result.usage()
    }


# Example usage
if __name__ == "__main__":
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
    print(result)