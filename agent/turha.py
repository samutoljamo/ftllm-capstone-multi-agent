# Code Review Agent
code_review_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a code review expert. You analyze code for bugs, readability, efficiency, '
        'and adherence to best practices. You provide specific, actionable feedback to improve code quality.'
    ),
  #  result_type=List[Dict[str, Any]]
)

# Testing Agent
testing_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a testing expert. You generate comprehensive test cases based on requirements '
        'and implementation details. You emphasize edge cases, security tests, and performance tests.'
    ),
 #   result_type=Dict[str, Any]
)

# Security Agent
security_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a security expert. You identify potential security vulnerabilities in code '
        'and provide recommendations to address them. You focus on OWASP Top 10 and other '
        'common security concerns.'
    ),
 #   result_type=List[Dict[str, str]]
)

# Performance Optimization Agent
optimization_agent = Agent(
    ollama_model,
    system_prompt=(
        'You are a performance optimization expert. You analyze code for inefficiencies '
        'and suggest improvements to enhance speed, reduce resource usage, and improve scalability.'
    ),
 #   result_type=List[Dict[str, Any]]
)


@coordinator_agent.tool
async def create_tests(ctx: RunContext[None], specifications: Dict[str, Any], code: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate test cases based on specifications and implementation.
    """
    specs_str = json.dumps(specifications, indent=2)
    code_str = json.dumps(code, indent=2)
    result = await testing_agent.run(
        f"Create comprehensive test cases based on these specifications and implementation:\n\nSpecifications:\n{specs_str}\n\nCode:\n{code_str}",
        usage=ctx.usage
    )
    return result.data


@coordinator_agent.tool
async def check_security(ctx: RunContext[None], code: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Analyze code for security vulnerabilities.
    """
    code_str = json.dumps(code, indent=2)
    result = await security_agent.run(
        f"Analyze this code for security vulnerabilities and provide recommendations:\n\n{code_str}",
        usage=ctx.usage
    )
    return result.data


@coordinator_agent.tool
async def optimize_performance(ctx: RunContext[None], code: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Analyze code for performance inefficiencies and suggest optimizations.
    """
    code_str = json.dumps(code, indent=2)
    result = await optimization_agent.run(
        f"Analyze this code for performance inefficiencies and suggest optimizations:\n\n{code_str}",
        usage=ctx.usage
    )
    return result.data