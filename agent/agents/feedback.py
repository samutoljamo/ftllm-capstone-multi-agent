from pydantic import BaseModel
from pydantic_ai import Agent
from .context import CodeGenerationDeps, FeedbackOutput
from tools.cypress_tests import read_cypress_tests
from tools.list_pages import list_all_pages
from tools.read_page import read_page

# Define the feedback agent directly without a creation function
feedback = Agent(
    deps_type=CodeGenerationDeps,
    result_type=FeedbackOutput,
    system_prompt=(
        "You are a feedback expert. Analyze the output and errors from the Cypress tests and Next.js server output, "
        "and provide actionable suggestions to improve the code and tests for better functionality and adherence to "
        "Next.js and Tailwind CSS best practices.\n\n"
        "Pay special attention to server logs from Next.js as they often contain critical information about errors "
        "that may not be visible in the frontend tests. Look for API errors, rendering issues, and other backend "
        "problems that might be causing test failures."
        "IMPORTANT: Before providing feedback, use the following tools to understand the code and tests better:"
        "- Use read_cypress_tests to understand the tests."
        "- Use read_page and list_all_pages to understand the pages."
        "If there are package issues, instruct that we do not allow any addiotional packages. Instruct the agent to remove the package from the code."
        "Create a short feedback message that mainly focuses on issues preventing the code from working rather than general feedback."
        "Common issues are:"
        "- Wrong imports"
        "- Using database directly in the api routes"
        "- Using wrong packages like sqlite instead of sqlite3 and axios instead of fetch"
    ),
    tools=[read_cypress_tests, read_page, list_all_pages]
)