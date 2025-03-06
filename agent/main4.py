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
        
        'Unlike a typical sequential development process, you should adapt to the specific needs of '
        'each project and make decisions that maximize the quality of the final product within the '
        'constraints provided.\n\n'
        
        'Think like an experienced tech lead who understands both the technical and project management '
        'aspects of software development. Consider tradeoffs between thoroughness and efficiency.'
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
async def coordinator_decide_next_action(
    ctx: RunContext[None], 
    current_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Decide the next action in the development process based on current state.
    Returns an action and reasoning for that action.
    """
    prompt = f"""
    You are the lead architect coordinating the development process. 
    Based on the current state, decide what action to take next.
    
    Current State:
    {json.dumps(current_state, indent=2)}
    
    Available Actions:
    1. "analyze_requirements" - Analyze user requirements (should be first step if no requirements exist)
    2. "generate_code" - Generate code based on requirements (requires requirements)
    3. "review_code" - Review the generated code (requires code)
    4. "create_tests" - Create tests for the code (requires code)
    5. "check_security" - Check for security vulnerabilities (requires code)
    6. "optimize_performance" - Identify performance optimizations (requires code)
    7. "make_improvements" - Improve code based on feedback (requires code and at least one type of issue)
    8. "finalize" - Complete the development process (should be called when code quality is satisfactory)
    
    Decide which action to take next and provide reasoning for your decision.
    Consider the prerequisites for each action and the current state of the development process.
    Think about what would be most valuable at this stage.
    
    Return a JSON object with two fields:
    - "action": The name of the action to perform (one of the available actions listed above)
    - "reasoning": A brief explanation of why you chose this action
    """
    
    result = await coordinator_agent.run(prompt, usage=ctx.usage)
    
    # Parse the response to extract action and reasoning
    try:
        decision = json.loads(result.data)
        # Validate that the decision contains the required fields
        if "action" not in decision or "reasoning" not in decision:
            raise ValueError("Decision missing required fields")
        return decision
    except Exception as e:
        # Fallback in case parsing fails
        print(f"Error parsing coordinator decision: {str(e)}")
        return {
            "action": "analyze_requirements" if not current_state.get("has_requirements") else "generate_code",
            "reasoning": "Fallback action due to parsing error"
        }

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


# Improved develop_software function that lets the coordinator make decisions
async def develop_software(user_request: str, language: str = "Python", max_iterations: int = 3) -> Dict[str, Any]:
    """
    Main function that allows the coordinator agent to drive the development process.
    
    Args:
        user_request: The user's software requirements or feature request
        language: The programming language to use for implementation
        max_iterations: Maximum number of iterations to prevent infinite loops
        
    Returns:
        A dictionary containing the full software development artifacts
    """
    dev_context = DevelopmentContext()
    
    # Create a consistent RunContext for all operations
    run_ctx = RunContext(None, "llama3.2", Usage(), "gffsdsdfd")
    
    # Initialize the context with the user request
    current_state = {
        "user_request": user_request,
        "language": language,
        "development_context": dev_context.to_dict(),
        "current_iteration": 1,
        "max_iterations": max_iterations
    }
    
    # Main coordination loop
    while current_state["current_iteration"] <= max_iterations:
        print(f"\n--- Starting iteration {current_state['current_iteration']} ---")
        
        # Ask coordinator to decide the next step
        next_action = await coordinator_decide_next_action(run_ctx, current_state)
        
        if next_action["action"] == "analyze_requirements":
            requirements = await analyze_requirements(
                run_ctx, user_request, dev_context.to_dict()
            )
            dev_context.requirements = requirements
            print("✅ Requirements analysis completed")
            
        elif next_action["action"] == "generate_code":
            code = await generate_code(
                run_ctx, 
                dev_context.requirements, 
                language, 
                dev_context.to_dict(),
                dev_context.review_issues if dev_context.review_issues else None
            )
            dev_context.code = code
            print("✅ Code generation completed")
            
        elif next_action["action"] == "review_code":
            review_issues = await review_code(
                run_ctx, dev_context.code, dev_context.requirements
            )
            dev_context.review_issues = review_issues
            print(f"✅ Code review completed - found {len(review_issues)} issues")
            
        elif next_action["action"] == "create_tests":
            test_cases = await create_tests(
                run_ctx, dev_context.requirements, dev_context.code
            )
            dev_context.test_cases = test_cases
            print("✅ Test creation completed")
            
        elif next_action["action"] == "check_security":
            security_issues = await check_security(
                run_ctx, dev_context.code, dev_context.requirements
            )
            dev_context.security_issues = security_issues
            print(f"✅ Security check completed - found {len(security_issues)} issues")
            
        elif next_action["action"] == "optimize_performance":
            performance_issues = await optimize_performance(
                run_ctx, dev_context.code, dev_context.requirements
            )
            dev_context.performance_issues = performance_issues
            print(f"✅ Performance optimization completed - found {len(performance_issues)} issues")
            
        elif next_action["action"] == "make_improvements":
            # Compile all issues
            all_issues = {
                "review_issues": dev_context.review_issues,
                "security_issues": dev_context.security_issues,
                "performance_issues": dev_context.performance_issues
            }
            
            improved_code = await make_improvements(
                run_ctx, dev_context.code, all_issues
            )
            dev_context.code = improved_code
            
            # Clear the issues lists since we've addressed them
            dev_context.review_issues = []
            dev_context.security_issues = []
            dev_context.performance_issues = []
            print("✅ Code improvements completed")
            
        elif next_action["action"] == "finalize":
            print("🎉 Development process completed successfully!")
            break
            
        # Save state after each step
        dev_context.save_state()
        
        # Update the current state for the next iteration
        current_state = {
            "user_request": user_request,
            "language": language,
            "development_context": dev_context.to_dict(),
            "current_iteration": dev_context.iteration,
            "max_iterations": max_iterations,
            "has_requirements": dev_context.requirements is not None,
            "has_code": dev_context.code is not None,
            "review_issues_count": len(dev_context.review_issues),
            "security_issues_count": len(dev_context.security_issues),
            "performance_issues_count": len(dev_context.performance_issues),
            "has_tests": dev_context.test_cases is not None,
            "last_action": next_action["action"],
            "last_action_reasoning": next_action["reasoning"]
        }
        
    # Final coordination summary
    summary_prompt = f"""
    Summarize the software development process for this project:
    
    Original request: {user_request}
    
    Implementation language: {language}
    
    Development iterations: {dev_context.iteration - 1}
    
    Development history: {json.dumps(dev_context.history, indent=2)}
    
    Provide a comprehensive overview of the final product, highlighting:
    1. Key features implemented
    2. Architecture and design decisions
    3. Notable code quality improvements made during iterations
    4. Remaining areas for future improvement
    """
    
    coordinator_result = await coordinator_agent.run(summary_prompt, usage=run_ctx.usage)
    
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
    print("Development Summary:")
    print(result["coordinator_summary"])
    print("\nUsage Statistics:")
    print(result["usage_stats"])