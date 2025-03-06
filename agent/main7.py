from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits, Usage
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from typing import Dict, List, Any, Optional, TypedDict, Literal
import json
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

# Shared development context – all detailed artifacts are saved here.
class DevelopmentContext:
    def __init__(self):
        self.requirements: Optional[RequirementsResult] = None
        self.code: Optional[CodeGenerationResult] = None
        self.review_issues: List[CodeReviewIssue] = []
        self.test_cases: Optional[TestingResult] = None
        self.security_issues: List[SecurityVulnerability] = []
        self.performance_issues: List[PerformanceIssue] = []
        self.summary: Optional[DevelopmentSummary] = None
        self.history: List[Dict[str, Any]] = []

    def save_state(self):
        self.history.append({
            "requirements": self.requirements,
            "code_files": None if not self.code else [f["filename"] for f in self.code["files"]],
            "review_issues_count": len(self.review_issues),
            "security_issues_count": len(self.security_issues),
            "performance_issues_count": len(self.performance_issues),
            "has_tests": self.test_cases is not None
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
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

# Common usage limits for all agents.
DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=10, total_tokens_limit=5000)

# Initialize the model (replace with your provider details).
ollama_model = OpenAIModel(
    model_name='deepseek-chat',
    provider=OpenAIProvider(base_url='https://api.deepseek.com')
)

# -------------------- Specialized Agents --------------------

requirements_agent = Agent(
    ollama_model,
    system_prompt=(
        "You are a requirements analysis expert. Given a user request, generate concise but detailed software "
        "specifications including functional and non-functional requirements, acceptance criteria, architecture "
        "recommendations, and a data model summary."
    ),
    result_type=RequirementsResult
)

code_generation_agent = Agent(
    ollama_model,
    system_prompt=(
        "You are a code generation expert. Generate clean, efficient, and well-commented code based on the "
        "provided software specifications. Produce an output that includes file names, setup instructions, and dependencies."
    ),
    result_type=CodeGenerationResult
)

code_review_agent = Agent(
    ollama_model,
    system_prompt=(
        "You are a code review expert. Review the provided code briefly and return an overview with the count of issues found."
    ),
    result_type=List[CodeReviewIssue]
)

testing_agent = Agent(
    ollama_model,
    system_prompt=(
        "You are a testing expert. Create a concise set of test cases based on the specifications and code. "
        "Return the overall testing strategy and the total count of tests."
    ),
    result_type=TestingResult
)

security_agent = Agent(
    ollama_model,
    system_prompt=(
        "You are a security expert. Identify potential security vulnerabilities in the code and return a summary "
        "with the count of vulnerabilities."
    ),
    result_type=List[SecurityVulnerability]
)

optimization_agent = Agent(
    ollama_model,
    system_prompt=(
        "You are a performance optimization expert. Briefly analyze the code for inefficiencies and return a summary "
        "with the count of performance issues found."
    ),
    result_type=List[PerformanceIssue]
)

# -------------------- Coordinator (Orchestrator) --------------------

coordinator_agent = Agent(
    ollama_model,
    system_prompt=(
        "You are the project coordinator. Your role is to orchestrate the entire software development process for the given user request. "
        "Using the available tools—analyze_requirements, generate_code, review_code, create_tests, check_security, optimize_performance, "
        "make_improvements, and generate_summary—execute each step exactly once in a single run. "
        "Do not return the full complex data; simply update the shared development context with detailed artifacts, and only return a lightweight summary."
    )
)

# -------------------- Coordinator Tools (Attached to the Coordinator) --------------------
# (Each tool updates the shared development context with full details.)

@coordinator_agent.tool
async def analyze_requirements(ctx: RunContext[DevelopmentContext], user_request: str) -> Dict[str, str]:
    prompt = f"Analyze the following user request for software requirements:\n{user_request}"
    result = await requirements_agent.run(prompt, usage=ctx.usage)
    ctx.context.requirements = result.data
    return {"status": "done", "summary": f"Requirements analysis complete: {len(result.data['functional_requirements'])} functional requirements identified."}

@coordinator_agent.tool
async def generate_code(ctx: RunContext[DevelopmentContext], language: str) -> Dict[str, str]:
    dev_context = ctx.context
    if dev_context.requirements is None:
        return {"status": "error", "summary": "Cannot generate code: requirements are missing."}
    specs_summary = f"Functional: {len(dev_context.requirements['functional_requirements'])}, Non-functional: {len(dev_context.requirements['non_functional_requirements'])}"
    prompt = f"Generate {language} code based on these requirements: {specs_summary}"
    result = await code_generation_agent.run(prompt, usage=ctx.usage)
    dev_context.code = result.data
    return {"status": "done", "summary": f"Code generation complete: {len(result.data['files'])} file(s) created."}

@coordinator_agent.tool
async def review_code(ctx: RunContext[DevelopmentContext]) -> Dict[str, str]:
    dev_context = ctx.context
    if dev_context.code is None or dev_context.requirements is None:
        return {"status": "error", "summary": "Cannot review code: missing code or requirements."}
    file_list = ", ".join(f["filename"] for f in dev_context.code["files"])
    prompt = f"Review the code in files: {file_list} against the requirements. Return only the count of issues found."
    result = await code_review_agent.run(prompt, usage=ctx.usage)
    dev_context.review_issues = result.data
    return {"status": "done", "summary": f"Code review complete: {len(result.data)} issue(s) found."}

@coordinator_agent.tool
async def create_tests(ctx: RunContext[DevelopmentContext]) -> Dict[str, str]:
    dev_context = ctx.context
    if dev_context.requirements is None or dev_context.code is None:
        return {"status": "error", "summary": "Cannot create tests: missing requirements or code."}
    file_list = ", ".join(f["filename"] for f in dev_context.code["files"])
    prompt = f"Create tests for the implementation in files: {file_list}. Provide a strategy and total count of tests."
    result = await testing_agent.run(prompt, usage=ctx.usage)
    dev_context.test_cases = result.data
    test_count = len(result.data.get("test_cases", []))
    return {"status": "done", "summary": f"Test creation complete: {test_count} test(s) generated."}

@coordinator_agent.tool
async def check_security(ctx: RunContext[DevelopmentContext]) -> Dict[str, str]:
    dev_context = ctx.context
    if dev_context.code is None or dev_context.requirements is None:
        return {"status": "error", "summary": "Cannot check security: missing code or requirements."}
    file_list = ", ".join(f["filename"] for f in dev_context.code["files"])
    prompt = f"Check the following files for security vulnerabilities: {file_list}. Return only the count of vulnerabilities."
    result = await security_agent.run(prompt, usage=ctx.usage)
    dev_context.security_issues = result.data
    return {"status": "done", "summary": f"Security check complete: {len(result.data)} vulnerability(ies) found."}

@coordinator_agent.tool
async def optimize_performance(ctx: RunContext[DevelopmentContext]) -> Dict[str, str]:
    dev_context = ctx.context
    if dev_context.code is None or dev_context.requirements is None:
        return {"status": "error", "summary": "Cannot optimize performance: missing code or requirements."}
    file_list = ", ".join(f["filename"] for f in dev_context.code["files"])
    prompt = f"Analyze performance issues in the following files: {file_list}. Return only the count of performance issues."
    result = await optimization_agent.run(prompt, usage=ctx.usage)
    dev_context.performance_issues = result.data
    return {"status": "done", "summary": f"Performance analysis complete: {len(result.data)} issue(s) found."}

@coordinator_agent.tool
async def make_improvements(ctx: RunContext[DevelopmentContext]) -> Dict[str, str]:
    dev_context = ctx.context
    if dev_context.code is None:
        return {"status": "error", "summary": "No code available for improvements."}
    issues_summary = {
        "review_issues": len(dev_context.review_issues),
        "security_issues": len(dev_context.security_issues),
        "performance_issues": len(dev_context.performance_issues)
    }
    prompt = f"Update the code to address these issues: {json.dumps(issues_summary)}. Return an updated codebase."
    result = await code_generation_agent.run(prompt, usage=ctx.usage)
    dev_context.code = result.data
    return {"status": "done", "summary": "Improvements applied: code updated based on feedback."}

@coordinator_agent.tool
async def generate_summary(ctx: RunContext[DevelopmentContext], user_request: str, language: str) -> DevelopmentSummary:
    dev_context = ctx.context
    file_names = [] if dev_context.code is None else [f["filename"] for f in dev_context.code["files"]]
    prompt = (
        f"Summarize the entire development process for the user request:\n{user_request}\n"
        f"Language: {language}\nFinal implemented files: {json.dumps(file_names)}\n"
        "Include key features, architectural decisions, improvements made, and suggestions for future work."
    )
    result = await coordinator_agent.run(prompt, usage=ctx.usage)
    try:
        summary_data = json.loads(result.data)
        return {
            "key_features": summary_data.get("key_features", []),
            "architecture": summary_data.get("architecture", ""),
            "improvements": summary_data.get("improvements", []),
            "future_work": summary_data.get("future_work", [])
        }
    except Exception:
        return {
            "key_features": ["Summary extraction failed"],
            "architecture": "Summary extraction failed",
            "improvements": ["Summary extraction failed"],
            "future_work": ["Summary extraction failed"]
        }

# -------------------- Single-Run Orchestration via the Coordinator --------------------

async def develop_software(user_request: str, language: str = "Python") -> Dict[str, Any]:
    """
    Run the full development process by simply running the coordinator agent once.
    The coordinator agent's prompt instructs it to call its attached tools internally, updating the shared context.
    """
    dev_context = DevelopmentContext()
    run_ctx = RunContext(dev_context, "llama3.2", Usage(), "unique-run-id")
    
    # The coordinator is invoked with a prompt that triggers the full process.
    coordinator_prompt = f"""
    You are the project coordinator. Orchestrate the full development process for the following user request:
    {user_request}
    Use the tools: analyze_requirements, generate_code, review_code, create_tests, check_security, 
    optimize_performance, make_improvements, and generate_summary. Execute each tool exactly once.
    Update the shared context with full details while only returning a lightweight summary.
    Indicate when the development process is complete.
    """
    result = await coordinator_agent.run(coordinator_prompt, usage=run_ctx.usage)
    print("Coordinator result:", result.data)
    
    # Save final state and return all artifacts from the shared context.
    dev_context.save_state()
    return {
        "requirements": dev_context.requirements,
        "code": dev_context.code,
        "tests": dev_context.test_cases,
        "review_issues": dev_context.review_issues,
        "security_issues": dev_context.security_issues,
        "performance_issues": dev_context.performance_issues,
        "development_history": dev_context.history,
        "summary": dev_context.summary
    }

# -------------------- Example Usage --------------------

if __name__ == "__main__":
    user_request = """
    Create a web API for a task management system with the following features:
    1. Users can create, read, update, and delete tasks.
    2. Tasks have a title, description, due date, priority, and status.
    3. Users can filter and sort tasks by various criteria.
    4. The system should validate inputs and handle errors gracefully.
    """
    
    result = asyncio.run(develop_software(user_request))
    
    print("\n== DEVELOPMENT COMPLETE ==")
    print(f"Requirements generated: {'Yes' if result['requirements'] else 'No'}")
    print(f"Code generated: {'Yes' if result['code'] else 'No'}")
    print(f"Tests generated: {'Yes' if result['tests'] else 'No'}")
    print(f"Review issues: {len(result['review_issues'])}")
    print(f"Security issues: {len(result['security_issues'])}")
    print(f"Performance issues: {len(result['performance_issues'])}")
    print("\nSummary:")
    print(json.dumps(result["summary"], indent=2))

    # save the result to a file
    with open("development_result.json", "w") as f:
        json.dump(result, f, indent=2)
