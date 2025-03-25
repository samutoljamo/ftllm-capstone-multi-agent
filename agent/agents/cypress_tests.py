from pydantic_ai import Agent
from .context import CypressTestsDeps
from tools.read_page import read_page
from tools.list_pages import list_all_pages
from tools.cypress_tests import read_cypress_tests, write_cypress_tests

# Define the cypress tests agent directly without a creation function
cypress_tests = Agent(
    deps_type=CypressTestsDeps,
    tools=[read_page, list_all_pages, read_cypress_tests, write_cypress_tests],
    system_prompt=(
        "You are a Cypress tests generation expert. Generate Cypress tests for the Next.js project. "
        "Use the read_page tool to examine the implementation of pages, and the write_cypress_tests tool "
        "to write your tests. You can also use list_all_pages to see what pages are available to test and read them with read_page. "
        "Ensure the tests cover critical functionalities and adhere to best practices. "
        "The path is relative to project root, do NOT USE a leading slash."
        "Do not rely on fixtures, the api will be available to test against."
    )
)