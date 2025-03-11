import subprocess
import os
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal, Any
import json
import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits, Usage
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv; load_dotenv()

# =======================
# Path Abstraction Helper
# =======================

class PathManager:
    """
    Handles path abstraction so agents don't deal with actual file paths.
    Maps virtual URLs to actual file paths.
    """
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()
        self.project_path = None
    
    def set_project_path(self, actual_path: str):
        """Set the actual project path for resolution"""
        self.project_path = actual_path
    
    def resolve_path(self, virtual_path: str) -> str:
        """Convert a virtual path like '/pages/index.js' to an actual file path"""
        if not self.project_path:
            raise ValueError("Project path not set. Call set_project_path first.")
        
        # Remove leading slash if present
        clean_path = virtual_path.lstrip('/')
        return os.path.join(self.project_path, clean_path)

# Initialize global path manager
path_manager = PathManager()

# =======================
# Data Models for Agents
# =======================

class CodeGenInput(BaseModel):
    page_description: str     # Description of what the page should do/look like
    feedback: Optional[str] = None  # Optional feedback from previous test runs

class FeedbackOutput(BaseModel):
    feedback_message: str
    suggestions: List[str]

# =======================
# Tool Interfaces (Python Functions)
# =======================

class ReadPageInput(BaseModel):
    url: str  # Virtual URL, e.g., "/pages/index.js"

class ReadPageOutput(BaseModel):
    content: str

def read_page(input: ReadPageInput) -> ReadPageOutput:
    actual_path = path_manager.resolve_path(input.url)
    try:
        with open(actual_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ReadPageOutput(content=content)
    except FileNotFoundError:
        return ReadPageOutput(content="")

class WritePageInput(BaseModel):
    url: str    # Virtual URL
    content: str

class WritePageOutput(BaseModel):
    success: bool
    message: Optional[str] = None

def write_page(input: WritePageInput) -> WritePageOutput:
    actual_path = path_manager.resolve_path(input.url)
    os.makedirs(os.path.dirname(actual_path), exist_ok=True)
    with open(actual_path, "w", encoding="utf-8") as f:
        f.write(input.content)
    return WritePageOutput(success=True, message=f"Page written successfully to {input.url}")

class ListPagesOutput(BaseModel):
    pages: List[str]  # List of virtual URLs

def list_all_pages() -> ListPagesOutput:
    if not path_manager.project_path:
        raise ValueError("Project path not set")
        
    pages_dir = os.path.join(path_manager.project_path, "pages")
    pages = []
    if os.path.exists(pages_dir):
        for root, _, files in os.walk(pages_dir):
            for file in files:
                if file.endswith(".js") or file.endswith(".tsx") or file.endswith(".jsx"):
                    actual_path = os.path.join(root, file)
                    # Convert to virtual URL
                    relative_path = os.path.relpath(actual_path, path_manager.project_path)
                    virtual_url = f"/{relative_path}"
                    pages.append(virtual_url)
    return ListPagesOutput(pages=pages)

class WriteCypressTestsInput(BaseModel):
    content: str

class WriteCypressTestsOutput(BaseModel):
    success: bool
    message: Optional[str] = None

def write_cypress_tests(input: WriteCypressTestsInput) -> WriteCypressTestsOutput:
    if not path_manager.project_path:
        raise ValueError("Project path not set")
        
    test_file_path = os.path.join(path_manager.project_path, "cypress", "integration", "tests.spec.js")
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(input.content)
    return WriteCypressTestsOutput(success=True, message="Cypress tests written successfully")

class ReadCypressTestsOutput(BaseModel):
    content: str

def read_cypress_tests() -> ReadCypressTestsOutput:
    if not path_manager.project_path:
        raise ValueError("Project path not set")
        
    test_file_path = os.path.join(path_manager.project_path, "cypress", "integration", "tests.spec.js")
    try:
        with open(test_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ReadCypressTestsOutput(content=content)
    except FileNotFoundError:
        return ReadCypressTestsOutput(content="")

# =======================
# Define AI Model and Usage Limits
# =======================

# Define a common usage limit for all agents
DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=100, total_tokens_limit=1000000)

# Initialize the model (adjust as needed for your environment)
ai_model = OpenAIModel(
    model_name='deepseek-chat', 
    provider=OpenAIProvider(base_url='https://api.deepseek.com')
)

# =======================
# Agent Definitions with Tools Attached
# =======================

# Code Generation Agent: Generates or updates page code using provided description
code_generation_agent = Agent(
    ai_model,
    deps_type=Dict[str, Any],  # Takes project description and feedback
    system_prompt=(
        "You are a Next.js code generation expert. Given a page description, generate or update the code for "
        "the specified application. Ensure the code follows Next.js conventions and uses Tailwind CSS for styling. "
        "If feedback is provided, incorporate it to improve the code. Use the read_page and write_page tools to "
        "interact with the project files and the list_all_pages tool to see what pages exist already."
    )
)

# Add tools to the code generation agent
@code_generation_agent.tool
async def read_page_tool(ctx: RunContext[Dict[str, Any]], url: str) -> str:
    """
    Read the content of a page from the project.
    
    Args:
        url: The virtual URL path of the page to read (e.g., '/pages/index.js')
        
    Returns:
        The content of the page, or empty string if the page doesn't exist
    """
    result = read_page(ReadPageInput(url=url))
    return result.content

@code_generation_agent.tool
async def write_page_tool(ctx: RunContext[Dict[str, Any]], url: str, content: str) -> str:
    """
    Write content to a page in the project.
    
    Args:
        url: The virtual URL path of the page to write (e.g., '/pages/index.js')
        content: The content to write to the page
        
    Returns:
        A success message if the write operation was successful
    """
    result = write_page(WritePageInput(url=url, content=content))
    return result.message

@code_generation_agent.tool
async def list_pages_tool(ctx: RunContext[Dict[str, Any]]) -> List[str]:
    """
    List all pages in the project.
    
    Returns:
        A list of virtual URL paths for all pages in the project
    """
    result = list_all_pages()
    return result.pages

# Cypress Tests Agent: Generates the Cypress tests file content for the project
cypress_tests_agent = Agent(
    ai_model,
    deps_type=Dict[str, Any],
    system_prompt=(
        "You are a Cypress tests generation expert. Generate Cypress tests for the Next.js project. "
        "Use the read_page tool to examine the implementation of pages, and the write_cypress_tests tool "
        "to write your tests. You can also use list_all_pages to see what pages are available to test. "
        "Ensure the tests cover critical functionalities and adhere to best practices."
    )
)

# Add tools to the cypress tests agent
@cypress_tests_agent.tool
async def read_page_tool(ctx: RunContext[Dict[str, Any]], url: str) -> str:
    """
    Read the content of a page from the project.
    
    Args:
        url: The virtual URL path of the page to read (e.g., '/pages/index.js')
        
    Returns:
        The content of the page, or empty string if the page doesn't exist
    """
    result = read_page(ReadPageInput(url=url))
    return result.content

@cypress_tests_agent.tool
async def write_cypress_tests_tool(ctx: RunContext[Dict[str, Any]], content: str) -> str:
    """
    Write Cypress tests for the project.
    
    Args:
        content: The content of the Cypress tests file
        
    Returns:
        A success message if the tests were written successfully
    """
    result = write_cypress_tests(WriteCypressTestsInput(content=content))
    return result.message

@cypress_tests_agent.tool
async def read_cypress_tests_tool(ctx: RunContext[Dict[str, Any]]) -> str:
    """
    Read the current Cypress tests for the project.
    
    Returns:
        The content of the Cypress tests file, or an empty string if it doesn't exist
    """
    result = read_cypress_tests()
    return result.content

@cypress_tests_agent.tool
async def list_pages_tool(ctx: RunContext[Dict[str, Any]]) -> List[str]:
    """
    List all pages in the project.
    
    Returns:
        A list of virtual URL paths for all pages in the project
    """
    result = list_all_pages()
    return result.pages

# Feedback Agent: Analyzes test outputs and provides suggestions
feedback_agent = Agent(
    ai_model,
    deps_type=Dict[str, Any],  # Takes test output and errors
    result_type=FeedbackOutput,
    system_prompt=(
        "You are a feedback expert. Analyze the output and errors from the Cypress tests, and provide actionable "
        "suggestions to improve the code and tests for better functionality and adherence to Next.js and Tailwind CSS best practices."
    )
)

# =======================
# Helper Functions (No LLM Involvement)
# =======================

def create_base_nextjs_project() -> None:
    """
    Creates a base Next.js project with Tailwind CSS using a predefined template.
    Sets the project path in the path manager.
    """
    # Create project directory
    actual_project_path = os.path.join(os.getcwd(), "nextjs-project")
    
    # Check if the directory already exists
    if os.path.exists(actual_project_path):
        print(f"Project directory already exists at {actual_project_path}")
    else:
        print(f"Creating new Next.js project at {actual_project_path}")
        
        # Create the directory structure
        os.makedirs(os.path.join(actual_project_path, "pages"), exist_ok=True)
        os.makedirs(os.path.join(actual_project_path, "cypress", "integration"), exist_ok=True)
        os.makedirs(os.path.join(actual_project_path, "styles"), exist_ok=True)
        os.makedirs(os.path.join(actual_project_path, "public"), exist_ok=True)
        os.makedirs(os.path.join(actual_project_path, "components"), exist_ok=True)

        # Create minimal package.json
        package_json = {
            "name": "nextjs-project",
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "cypress": "cypress open",
                "cypress:run": "cypress run"
            },
            "dependencies": {
                "next": "^12.0.0",
                "react": "^17.0.2",
                "react-dom": "^17.0.2",
                "tailwindcss": "^3.0.0"
            },
            "devDependencies": {
                "cypress": "^9.2.0",
                "autoprefixer": "^10.4.0",
                "postcss": "^8.4.5"
            }
        }
        
        with open(os.path.join(actual_project_path, "package.json"), "w") as f:
            json.dump(package_json, f, indent=2)
            
        # Create tailwind.config.js
        tailwind_config = """module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
        with open(os.path.join(actual_project_path, "tailwind.config.js"), "w") as f:
            f.write(tailwind_config)
            
        # Create postcss.config.js
        postcss_config = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
        with open(os.path.join(actual_project_path, "postcss.config.js"), "w") as f:
            f.write(postcss_config)
            
        # Create global.css with Tailwind imports
        global_css = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
        with open(os.path.join(actual_project_path, "styles", "globals.css"), "w") as f:
            f.write(global_css)
            
        # Create bare minimum _app.js to import the global styles
        app_js = """import '../styles/globals.css'

function MyApp({ Component, pageProps }) {
  return <Component {...pageProps} />
}

export default MyApp
"""
        with open(os.path.join(actual_project_path, "pages", "_app.js"), "w") as f:
            f.write(app_js)
            
        # Create cypress.json config
        cypress_json = {
            "baseUrl": "http://localhost:3000",
            "video": False
        }
        with open(os.path.join(actual_project_path, "cypress.json"), "w") as f:
            json.dump(cypress_json, f, indent=2)
    
    # Set the project path in the path manager
    path_manager.set_project_path(actual_project_path)

def run_cypress_tests() -> Dict[str, any]:
    """
    Runs Cypress tests for the project using a shell command.
    Returns a dictionary with success status, output, and errors.
    """
    if not path_manager.project_path:
        raise ValueError("Project path not set")
    
    # Ensure the test file exists
    test_file_path = os.path.join(path_manager.project_path, "cypress", "integration", "tests.spec.js")
    if not os.path.exists(test_file_path):
        return {
            "success": False,
            "output": "",
            "errors": ["No test file found. Please generate Cypress tests first."]
        }
    
    try:
        # First, ensure the development server is running
        # Note: In a real implementation, you would check if the server is already running
        # and start it only if needed, in a separate process

        # Run Cypress tests in headless mode
        print("Running Cypress tests...")
        result = subprocess.run(
            ["npx", "cypress", "run", "--headless"],
            cwd=path_manager.project_path,
            capture_output=True,
            text=True,
            timeout=60  # Timeout after 60 seconds
        )
        
        # Process the result
        success = result.returncode == 0
        
        return {
            "success": success,
            "output": result.stdout,
            "errors": [result.stderr] if result.stderr else []
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Test execution timed out",
            "errors": ["Cypress test execution timed out after 60 seconds"]
        }
    except subprocess.SubprocessError as e:
        return {
            "success": False,
            "output": "",
            "errors": [f"Error running Cypress tests: {str(e)}"]
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": [f"Unexpected error: {str(e)}"]
        }

# =======================
# Simplified development flow with direct agent invocation using the tools
# =======================

async def generate_code_with_tools(project_description: str, feedback: Optional[str] = None) -> None:
    """Generate code for the Next.js application using the code generation agent with tools"""
    print("Generating code...")
    
    # Prepare input for the code generation agent
    input_data = {
        "project_description": project_description,
        "feedback": feedback
    }
    
    # Call code generation agent - instead of returning files, it will use tools to write them
    await code_generation_agent.run(
        json.dumps(input_data),
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    print(f"Code generation completed, files written to project")

async def generate_cypress_tests_with_tools() -> None:
    """Generate Cypress tests for the application using the cypress tests agent with tools"""
    print("Generating Cypress tests...")
    
    # Call cypress tests agent - it will use tools to read pages and write tests
    await cypress_tests_agent.run(
        json.dumps({"action": "generate_tests"}),
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    print("Cypress tests generation completed")

async def get_feedback(test_output: str, test_errors: List[str]) -> FeedbackOutput:
    """Get feedback based on test results"""
    print("Getting feedback on test results...")
    
    # Prepare input for the feedback agent
    input_data = {
        "test_output": test_output,
        "test_errors": test_errors
    }
    
    # Call feedback agent
    result = await feedback_agent.run(
        json.dumps(input_data),
        usage_limits=DEFAULT_USAGE_LIMITS
    )
    
    return result.data

async def full_development_flow(project_description: str, max_iterations: int = 3):
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
    create_base_nextjs_project()
    print("Created base Next.js project")
    
    # Create a usage tracker for token usage
    usage = Usage()
    
    # Store development artifacts
    feedback_result = None
    history = []
    
    # Main development loop
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration}/{max_iterations} ---")
        
        # Step 2: Generate or update code based on feedback
        await generate_code_with_tools(
            project_description, 
            feedback_result.feedback_message if feedback_result else None
        )
        print(f"Generated code in iteration {iteration}")
        
        # Step 3: Generate Cypress tests
        await generate_cypress_tests_with_tools()
        print("Generated Cypress tests")
        
        # Step 4: Run tests and get feedback
        test_result = run_cypress_tests()
        print(f"Tests ran with success={test_result['success']}")
        
        # Save the state of this iteration
        pages = list_all_pages().pages
        history.append({
            "iteration": iteration,
            "pages": pages,
            "test_success": test_result['success'],
            "test_errors": test_result['errors']
        })
        
        # If tests pass, we're done
        if test_result['success']:
            print("Tests passed successfully!")
            break
        
        # If tests fail, get feedback for next iteration
        feedback_result = await get_feedback(test_result['output'], test_result['errors'])
        print(f"Feedback: {feedback_result.feedback_message}")
        print(f"Suggestions: {feedback_result.suggestions}")
        
        # If this was the last iteration, we're done even if tests failed
        if iteration == max_iterations:
            print(f"Reached maximum iterations ({max_iterations})")
    
    # Return development results
    return {
        "pages": list_all_pages().pages,
        "cypress_tests": read_cypress_tests().content,
        "feedback": feedback_result.dict() if feedback_result else None,
        "history": history,
        "iterations_completed": iteration,
        "tests_passed": test_result['success'] if 'test_result' in locals() else False,
        "project_path": path_manager.project_path
    }

# Example usage
if __name__ == "__main__":
    # Example project description
    project_description = """
    Create a basic Next.js application that displays a list of blog posts. 
    Each post should have a title, author, date, and content. 
    Users should be able to click on a post to view its full content.
    The application should have a clean, responsive design using Tailwind CSS.
    """
    
    # Run the development process with direct agent invocation using tools
    result = asyncio.run(full_development_flow(project_description))
    
    # Save results to a file
    with open("development_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("Development results saved to development_result.json")
    print(f"Next.js project created at: {result['project_path']}")
    print("\nTo run the application:")
    print(f"cd {result['project_path']}")
    print("npm install")
    print("npm run dev")
