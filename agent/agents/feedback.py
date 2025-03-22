from pydantic import BaseModel
from pydantic_ai import Agent
from .context import FeedbackDeps, FeedbackOutput

# Define the feedback agent directly without a creation function
feedback = Agent(
    deps_type=FeedbackDeps,
    result_type=FeedbackOutput,
    system_prompt=(
        "You are a feedback expert. Analyze the output and errors from the Cypress tests and Next.js server output, "
        "and provide actionable suggestions to improve the code and tests for better functionality and adherence to "
        "Next.js and Tailwind CSS best practices.\n\n"
        "Pay special attention to server logs from Next.js as they often contain critical information about errors "
        "that may not be visible in the frontend tests. Look for API errors, rendering issues, and other backend "
        "problems that might be causing test failures."
    )
    # No tools are required for the feedback agent as it just processes the input and generates suggestions
)