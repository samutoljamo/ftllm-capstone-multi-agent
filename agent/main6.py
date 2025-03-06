from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits, Usage
from typing import Dict, List, Any, Optional, TypedDict, Literal
import json
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv; load_dotenv()

import logfire


logfire.configure()
logfire.instrument_pydantic() 

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

class DevelopmentSummary(TypedDict):
    key_features: List[str]
    architecture: str
    improvements: List[str]
    future_work: List[str]

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
            "code_files": None if not self.code else [f["filename"] for f in self.code["files"]],
            "review_issues_count": len(self.review_issues),
            "security_issues_count": len(self.security_issues),
            "performance_issues_count": len(self.performance_issues),
            "has_tests": self.test_cases is not None
        })
        self.iteration += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for passing to agents"""
        return {
            "iteration": self.iteration,
            "has_requirements": self.requirements is not None,
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
    model_name='deepseek-chat', provider=OpenAIProvider(base_url='https://api.deepseek.com')
)

# Requirements Analysis Agent
requirements_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a requirements analysis expert. Given a user request, you generate detailed '
        'software specifications including functional requirements, non-functional requirements, '
        'and acceptance criteria. Be thorough yet concise. The result is an object containing arrays of strings.'
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

# Project Coordination Agent - IMPROVED PROMPT
coordinator_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are the lead software architect and project manager coordinating an AI-driven software '
        'development process. Your role is to make strategic decisions about what steps should be taken '
        'next based on the current state of development.\n\n'
        
        'Your responsibilities include:\n'
        '1. Analyzing the current development context to determine the most valuable next step\n'
        '2. Making informed decisions about when to perform requirements analysis, code generation, '
        'testing, security checks, and other development activities\n'
        '3. Determining when issues need to be fixed before proceeding to the next steps\n'
        '4. Deciding when the development process is complete\n'
        '5. Providing clear reasoning for each decision you make\n\n'
        
        'You have access to specialized tools for each phase of development. Use these tools as needed:\n'
        '- analyze_requirements: When you need detailed specifications from a user request\n'
        '- generate_code: When you need to create or update code based on specifications\n'
        '- review_code: When you need to evaluate code quality and identify issues\n'
        '- create_tests: When you need to develop tests for the implemented code\n'
        '- check_security: When you need to identify security vulnerabilities\n'
        '- optimize_performance: When you need to find performance bottlenecks\n'
        '- make_improvements: When you need to fix issues identified in the code\n'
        '- generate_summary: When the development is complete and you need a final summary\n\n'
        
        'Call these tools directly rather than trying to perform their functions yourself. You are '
        'the orchestrator, not the implementer. Focus on making the right decisions about which '
        'tools to use when, and let the specialized agents handle the details.\n\n'
        
        'Your goal is to deliver high-quality software that meets all requirements through an '
        'efficient development process.'
    )
)

# Add tools to the coordinator agent
@coordinator_agent.tool
async def analyze_requirements(
    ctx: RunContext[None], 
    user_request: str
) -> RequirementsResult:
    """
    Analyze user requirements and generate detailed software specifications.
    
    Args:
        user_request: The raw user request describing what they want built
        
    Returns:
        A structured requirements document with functional requirements, non-functional 
        requirements, acceptance criteria, architecture recommendations, and data model.
    """
    prompt = f"""
    Analyze the following user request and generate detailed software specifications.
    
    User Request:
    {user_request}
    
    Return a structured specification document including:
    1. Functional requirements (what the system should do)
    2. Non-functional requirements (performance, security, usability, etc.)
    3. Acceptance criteria (how to verify the requirements are met)
    4. Architecture recommendations
    5. Data model (entities and relationships)
    """
    
    result = await requirements_agent.run(prompt, usage=ctx.usage)
    return result.data


@coordinator_agent.tool
async def generate_code(
    ctx: RunContext[None], 
    specifications: RequirementsResult, 
    language: str,
    review_feedback: Optional[List[CodeReviewIssue]] = None
) -> CodeGenerationResult:
    """
    Generate code based on software specifications and optional review feedback.
    
    Args:
        specifications: The requirements specification to implement
        language: The programming language to use
        review_feedback: Optional list of review issues to address
        
    Returns:
        Generated code files with setup instructions and dependencies
    """
    specs_str = json.dumps(specifications, indent=2)
    feedback_str = "None" if not review_feedback else json.dumps(review_feedback, indent=2)
    
    prompt = f"""
    Generate {language} code based on these specifications:
    
    Specifications:
    {specs_str}
    
    Previous Review Feedback (address these issues):
    {feedback_str}
    
    Create a complete implementation that satisfies all requirements.
    Organize your code into appropriate files and modules.
    Include setup instructions and dependencies.
    """
    
    result = await code_generation_agent.run(prompt, usage=ctx.usage)
    return result.data


@coordinator_agent.tool
async def review_code(
    ctx: RunContext[None], 
    code: CodeGenerationResult, 
    specifications: RequirementsResult
) -> List[CodeReviewIssue]:
    """
    Review generated code and provide feedback.
    
    Args:
        code: The code to review
        specifications: The requirements the code should meet
        
    Returns:
        A list of code review issues with severity, location, and recommendations
    """
    code_files = "\n\n".join([
        f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" 
        for f in code['files']
    ])
    specs_str = json.dumps(specifications, indent=2)
    
    prompt = f"""
    Review the following code and provide detailed feedback:
    
    Code Implementation:
    {code_files}
    
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
    
    result = await code_review_agent.run(prompt, usage=ctx.usage)
    return result.data


@coordinator_agent.tool
async def create_tests(
    ctx: RunContext[None], 
    specifications: RequirementsResult, 
    code: CodeGenerationResult
) -> TestingResult:
    """
    Generate test cases based on specifications and implementation.
    
    Args:
        specifications: The requirements specification
        code: The code implementation to test
        
    Returns:
        A comprehensive testing plan with test cases and coverage metrics
    """
    code_files = "\n\n".join([
        f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" 
        for f in code['files']
    ])
    specs_str = json.dumps(specifications, indent=2)
    
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
    
    result = await testing_agent.run(prompt, usage=ctx.usage)
    return result.data


@coordinator_agent.tool
async def check_security(
    ctx: RunContext[None], 
    code: CodeGenerationResult, 
    specifications: RequirementsResult
) -> List[SecurityVulnerability]:
    """
    Analyze code for security vulnerabilities.
    
    Args:
        code: The code to check for security issues
        specifications: The requirements specification with security expectations
        
    Returns:
        A list of security vulnerabilities with severity, category, and recommendations
    """
    code_files = "\n\n".join([
        f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" 
        for f in code['files']
    ])
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
    
    result = await security_agent.run(prompt, usage=ctx.usage)
    return result.data


@coordinator_agent.tool
async def optimize_performance(
    ctx: RunContext[None], 
    code: CodeGenerationResult, 
    specifications: RequirementsResult
) -> List[PerformanceIssue]:
    """
    Analyze code for performance inefficiencies and suggest optimizations.
    
    Args:
        code: The code to check for performance issues
        specifications: The requirements specification with performance expectations
        
    Returns:
        A list of performance issues with severity, type, and recommendations
    """
    code_files = "\n\n".join([
        f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" 
        for f in code['files']
    ])
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
    
    result = await optimization_agent.run(prompt, usage=ctx.usage)
    return result.data


@coordinator_agent.tool
async def make_improvements(
    ctx: RunContext[None],
    code: CodeGenerationResult,
    review_issues: List[CodeReviewIssue],
    security_issues: List[SecurityVulnerability],
    performance_issues: List[PerformanceIssue]
) -> CodeGenerationResult:
    """
    Improve code based on review, security, and performance feedback.
    
    Args:
        code: The code to improve
        review_issues: Code review issues to address
        security_issues: Security vulnerabilities to fix
        performance_issues: Performance issues to optimize
        
    Returns:
        Improved code with issues addressed
    """
    # Compile all issues
    all_issues = {
        "review_issues": review_issues,
        "security_issues": security_issues,
        "performance_issues": performance_issues
    }
    
    code_files = "\n\n".join([
        f"File: {f['filename']}\n```{f['language']}\n{f['content']}\n```" 
        for f in code['files']
    ])
    issues_str = json.dumps(all_issues, indent=2)
    
    prompt = f"""
    Update the following code to address the identified issues:
    
    Original Code:
    {code_files}
    
    Issues to Address:
    {issues_str}
    
    Make all necessary changes to fix the issues while maintaining the original functionality.
    Return the complete updated codebase, not just the changes.
    """
    
    result = await code_generation_agent.run(prompt, usage=ctx.usage)
    return result.data


@coordinator_agent.tool
async def generate_summary(
    ctx: RunContext[None],
    user_request: str,
    language: str,
    iteration_count: int,
    requirements: RequirementsResult,
    code_files: List[str]
) -> DevelopmentSummary:
    """
    Generate a comprehensive summary of the completed development process.
    
    Args:
        user_request: The original user request
        language: The programming language used
        iteration_count: Number of development iterations performed
        requirements: The final requirements specification
        code_files: List of code files created
        
    Returns:
        A summary of the development process highlighting key features, architecture, 
        improvements, and future work
    """
    prompt = f"""
    Summarize the software development process for this project:
    
    Original request: {user_request}
    
    Implementation language: {language}
    
    Development iterations: {iteration_count}
    
    Requirements: {json.dumps(requirements, indent=2)}
    
    Implemented files: {json.dumps(code_files, indent=2)}
    
    Provide a comprehensive overview of the final product, highlighting:
    1. Key features implemented
    2. Architecture and design decisions
    3. Notable code quality improvements made during iterations
    4. Remaining areas for future improvement
    
    Format your response as a structured summary with specific sections for each of these areas.
    """
    
    result = await coordinator_agent.run(prompt, usage=ctx.usage)
    
    # Try to parse the response as structured data
    try:
        summary_data = json.loads(result.data)
        return {
            "key_features": summary_data.get("key_features", []),
            "architecture": summary_data.get("architecture", ""),
            "improvements": summary_data.get("improvements", []),
            "future_work": summary_data.get("future_work", [])
        }
    except:
        # Fallback for unstructured response
        return {
            "key_features": ["Features extraction failed"],
            "architecture": "Architecture extraction failed",
            "improvements": ["Improvements extraction failed"],
            "future_work": ["Future work extraction failed"]
        }


async def develop_software(user_request: str, language: str = "Python", max_iterations: int = 3) -> Dict[str, Any]:
    """
    Main function that orchestrates the development process.
    
    Args:
        user_request: The user's software requirements or feature request
        language: The programming language to use for implementation
        max_iterations: Maximum number of iterations to prevent infinite loops
        
    Returns:
        A dictionary containing the full software development artifacts
    """
    # Create a development context to track state
    dev_context = DevelopmentContext()
    
    # Create a consistent RunContext for all operations
    run_ctx = RunContext(None, "llama3.2", Usage(), "gffsdsdfd")
    
    # Initial prompt for the coordinator
    coordinator_prompt = f"""
    You are the lead architect for a software development project. Your goal is to coordinate 
    the development of software based on the following user request:
    
    ```
    {user_request}
    ```
    
    You should deliver a high-quality implementation in {language} within {max_iterations} iterations.
    
    You have access to specialized tools for each phase of development. Call these tools directly 
    as needed to complete the development process efficiently:
    
    - analyze_requirements: Get detailed specifications from a user request
    - generate_code: Create code based on specifications
    - review_code: Evaluate code quality and identify issues
    - create_tests: Develop tests for the implemented code
    - check_security: Identify security vulnerabilities
    - optimize_performance: Find performance bottlenecks
    - make_improvements: Fix issues identified in the code
    - generate_summary: Create a final summary when development is complete
    
    Start by analyzing the requirements, then proceed with the development process as you see fit.
    Think about the best order of operations and which tools you need to use at each step.
    
    The development context is initially empty as we're just starting.
    """
    
    # Let the coordinator drive the process
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Starting iteration {iteration}/{max_iterations} ---")
        
        # Update the prompt with current context if we're beyond the first iteration
        if iteration > 1:
            context_str = json.dumps(dev_context.to_dict(), indent=2)
            coordinator_prompt = f"""
            Continue coordinating the development of software based on the user request:
            
            ```
            {user_request}
            ```
            
            Current development context:
            {context_str}
            
            Remember your goal is to deliver a high-quality implementation in {language}.
            You've completed {iteration-1} iterations so far, with {max_iterations-iteration+1} remaining.
            
            Use your tools wisely to make the most progress in this iteration:
            - analyze_requirements: Get detailed specifications from a user request
            - generate_code: Create code based on specifications
            - review_code: Evaluate code quality and identify issues
            - create_tests: Develop tests for the implemented code
            - check_security: Identify security vulnerabilities
            - optimize_performance: Find performance bottlenecks
            - make_improvements: Fix issues identified in the code
            - generate_summary: Create a final summary when development is complete
            
            If the code is of high quality with no major issues and the requirements are met, you can consider the development complete.
            """
        
        # Get the coordinator's response
        coordinator_response = await coordinator_agent.run(coordinator_prompt, usage=run_ctx.usage)
        
        # Save the current state
        dev_context.save_state()
    
    # After development is complete, generate a final summary
    if dev_context.requirements and dev_context.code:
        code_files = [f["filename"] for f in dev_context.code["files"]]
        summary = await generate_summary(
            run_ctx, 
            user_request, 
            language, 
            dev_context.iteration,
            dev_context.requirements,
            code_files
        )
    else:
        summary = {
            "key_features": ["Development incomplete"],
            "architecture": "Development incomplete",
            "improvements": ["Development incomplete"],
            "future_work": ["Complete the initial development"]
        }
    
    # Return the final artifacts
    return {
        "requirements": dev_context.requirements,
        "code": dev_context.code,
        "tests": dev_context.test_cases,
        "review_issues": dev_context.review_issues,
        "security_issues": dev_context.security_issues,
        "performance_issues": dev_context.performance_issues,
        "development_history": dev_context.history,
        "summary": summary
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
    print("\n== DEVELOPMENT COMPLETE ==")
    print(f"Requirements: {'Yes' if result['requirements'] else 'No'}")
    print(f"Code: {'Yes' if result['code'] else 'No'}")
    print(f"Tests: {'Yes' if result['tests'] else 'No'}")
    print(f"Final issues: {len(result['review_issues'])} review, {len(result['security_issues'])} security, {len(result['performance_issues'])} performance")
    
    print("\nSummary:")
    print(json.dumps(result["summary"], indent=2))