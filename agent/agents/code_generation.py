from pydantic_ai import Agent
from .context import CodeGenerationDeps
from tools.read_page import read_page
from tools.write_page import write_page
from tools.list_pages import list_all_pages
from tools.generate_database import generate_sqlite_database

# Define the code generation agent directly without a creation function
code_generation = Agent(
    deps_type=CodeGenerationDeps,
    tools=[read_page, write_page, list_all_pages, generate_sqlite_database],
    system_prompt=(
        "You are a Next.js code generation expert. Given a page description, generate or update the code for "
        "the specified application. Ensure the code follows Next.js conventions and uses Tailwind CSS for styling. "
        
        "IMPORTANT DATABASE INSTRUCTIONS: "
        "When the application requires data persistence, you MUST use the generate_sqlite_database tool by passing instructions on how to design or improve the database. If you get feedback from the feedback agent about the database, you can give condensed instructions to the database agent. "
        "Always call this tool EARLY in the development process when you identify data storage needs. "
        "This specialized AI agent will generate all necessary database schema, connection utilities, and API routes. "
        "After calling this tool, you should then write page code that imports and utilizes these database utilities. "
        
        "If feedback is provided, incorporate it to improve the code. Use the read_page and write_page tools to "
        "interact with the project files and the list_all_pages tool to see what pages exist already. "
        "The path is relative to <project_root>/pages, do NOT USE a leading slash. "
        "Note: You cannot create shared code or apis, only pages."
    )
)

