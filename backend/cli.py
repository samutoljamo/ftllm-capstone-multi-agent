# Example usage

import asyncio
from dotenv import load_dotenv; load_dotenv()
from agent.main import full_development_flow

if __name__ == "__main__":
    # Example project description
    project_description = """
Create a simple Next.js application for a personal recipe collection. 
The application should display a grid of recipe cards, each showing an image, title, preparation time, and difficulty level.
Users should be able to click on a recipe card to view the full details including ingredients, instructions, and serving size.
Implement sorting options to filter recipes by preparation time, difficulty, or newest additions.
The application should feature a responsive, modern design using Tailwind CSS with an appealing color scheme suitable for a food-related website.
    """
    
    # Run the development process with direct agent invocation using tools
    result = asyncio.run(full_development_flow(project_description))
    
    print(f"Development completed after {result['iterations_completed']} iterations")
    print(f"Tests passed: {result['tests_passed']}")
    print(f"Next.js project created at: {result['final_project_path']}")
    print("\nTo run the application:")
    print(f"cd {result['final_project_path']}")
    print("npm install")
    print("npm run dev")