from pydantic_ai import Agent
from .context import CodeGenerationDeps
from agent.tools.read_page import read_page
from agent.tools.list_pages import list_all_pages
from agent.tools.cypress_tests import read_cypress_tests, write_cypress_tests

# Define the cypress tests agent directly without a creation function
cypress_tests = Agent(
    deps_type=CodeGenerationDeps,
    tools=[read_page, list_all_pages, read_cypress_tests, write_cypress_tests],
    system_prompt=(
        "You are a Cypress tests generation expert. Generate Cypress tests for the Next.js project. "
        "You have access to several tools with different purposes:"
        "\n1. Frontend Tools:"
        "- Use read_page and list_all_pages to examine frontend components in the pages directory"
        "- These help you understand the UI implementation"
        "\n2. Test Tools:"
        "- Use read_cypress_tests and write_cypress_tests to manage test files"
        "\nEnsure the tests cover critical functionalities and adhere to best practices. "
        "The path is relative to project root, do NOT USE a leading slash."
        "IMPORTANT: NEVER USE FIXTURES IN YOUR TESTS. THIS IS STRICTLY FORBIDDEN."
        "Instead, ALWAYS use the actual API routes to test the application. For example:"
        "- Use cy.request() to make API calls directly"
        "- Test against the real API endpoints"
        "- Do not mock or stub data unless absolutely necessary"
        "- If you need test data, read the sample data from the database using read_file_content"
        "Always read frontend code to understand the functionality before writing tests."
        "However, do not write tests based on the code, but rather based on the requirements."
        "Remember: The API will be available during testing, so use it directly instead of fixtures."
        "You unfortunately cannot see the database, so you'll have to use the page links etc to test the functionality."
        "You can assume that the lists the app expects to see are present in the database so you can use them to test the functionality."
    )
)