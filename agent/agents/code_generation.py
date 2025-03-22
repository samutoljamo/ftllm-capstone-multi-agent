from pydantic_ai import Agent
from .context import CodeGenerationDeps
from tools.read_page import read_page
from tools.write_page import write_page
from tools.list_pages import list_all_pages

# Define the code generation agent directly without a creation function
code_generation = Agent(
    deps_type=CodeGenerationDeps,
    tools=[read_page, write_page, list_all_pages],
    system_prompt=(
        "You are a Next.js code generation expert. Given a page description, generate or update the code for "
        "the specified application. Ensure the code follows Next.js conventions and uses Tailwind CSS for styling. "
        "If feedback is provided, incorporate it to improve the code. Use the read_page and write_page tools to "
        "interact with the project files and the list_all_pages tool to see what pages exist already."
        "The path is relative to <project_root>/pages, do NOT USE a leading slash."
        "Note: You cannot create shared code or apis, only pages."
    )
)
