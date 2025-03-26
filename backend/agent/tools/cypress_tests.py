from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Optional
import os
from .tool_notifier import tool_notifier

class WriteCypressTestsInput(BaseModel):
    content: str

class WriteCypressTestsOutput(BaseModel):
    success: bool
    message: Optional[str] = None

class ReadCypressTestsOutput(BaseModel):
    content: str

async def _write_cypress_tests(ctx: RunContext, input: WriteCypressTestsInput) -> WriteCypressTestsOutput:
    print("Writing Cypress tests")
    project_path = ctx.deps.project_path
    
    # Ensure cypress directory exists
    cypress_dir = os.path.join(project_path, "cypress", "e2e")
    os.makedirs(cypress_dir, exist_ok=True)
    
    # Write the tests to the standard test file
    test_file_path = os.path.join(cypress_dir, "app.cy.js")
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(input.content)
        
    return WriteCypressTestsOutput(
        success=True, 
        message=f"Cypress tests written successfully to {test_file_path}"
    )

async def _read_cypress_tests(ctx: RunContext) -> ReadCypressTestsOutput:
    print("Reading Cypress tests")
    project_path = ctx.deps.project_path
    
    test_file_path = os.path.join(project_path, "cypress", "e2e", "app.cy.js")
    
    try:
        with open(test_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ReadCypressTestsOutput(content=content)
    except FileNotFoundError:
        return ReadCypressTestsOutput(content="")

# Export the tools
write_cypress_tests = Tool(tool_notifier(_write_cypress_tests))
read_cypress_tests = Tool(tool_notifier(_read_cypress_tests))