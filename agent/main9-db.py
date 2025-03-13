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
# Data Models for SQLite Tool
# =======================

class SetupSQLiteInput(BaseModel):
    """Input for setting up SQLite database"""
    schema_content: str  # SQL schema content
    include_auth: bool = True
    include_session: bool = True
    database_name: str = "blog.db"

class SetupSQLiteOutput(BaseModel):
    """Output for setting up SQLite database"""
    success: bool
    message: Optional[str] = None
    created_files: List[str] = []

def setup_sqlite_database(input: SetupSQLiteInput) -> SetupSQLiteOutput:
    """
    Sets up SQLite database in the Next.js project.
    
    Args:
        input: Configuration for SQLite setup
        
    Returns:
        SetupSQLiteOutput with success status and created files
    """
    if not path_manager.project_path:
        return SetupSQLiteOutput(
            success=False,
            message="Project path not set. Call set_project_path first."
        )
    
    created_files = []
    
    try:
        # Step 1: Create db directory and schema file
        db_dir = os.path.join(path_manager.project_path, "db")
        os.makedirs(db_dir, exist_ok=True)
        
        schema_path = os.path.join(db_dir, "schema.sql")
        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(input.schema_content)
        created_files.append("/db/schema.sql")
        
        # Step 2: Create data directory for database file
        data_dir = os.path.join(path_manager.project_path, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Step 3: Add SQLite dependencies to package.json
        package_json_path = os.path.join(path_manager.project_path, "package.json")
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)
                
            # Required dependencies
            dependencies = {
                "better-sqlite3": "^8.6.0"
            }
            
            # Optional dependencies
            if input.include_auth:
                dependencies.update({
                    "bcryptjs": "^2.4.3"
                })
            
            if input.include_session:
                dependencies.update({
                    "iron-session": "^6.3.1"
                })
            
            # Update dependencies
            if "dependencies" not in package_data:
                package_data["dependencies"] = {}
            
            package_data["dependencies"].update(dependencies)
            
            with open(package_json_path, "w", encoding="utf-8") as f:
                json.dump(package_data, f, indent=2)
        except (FileNotFoundError, json.JSONDecodeError):
            return SetupSQLiteOutput(
                success=False,
                message="package.json not found or invalid. Please ensure a valid package.json exists in the project root.",
                created_files=created_files
            )
        
        # Step 4: Create database library files
        lib_dir = os.path.join(path_manager.project_path, "lib")
        os.makedirs(lib_dir, exist_ok=True)
        
        # Create db.js - main database connection file
        db_js_content = f"""// SQLite database connection using better-sqlite3
import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

// Ensure the data directory exists
const dataDir = path.join(process.cwd(), 'data');
if (!fs.existsSync(dataDir)) {{
  fs.mkdirSync(dataDir, {{ recursive: true }});
}}

// Database file path
const dbPath = path.join(dataDir, '{input.database_name}');

// Create and initialize the database
let db;

try {{
  db = new Database(dbPath);
  
  // Enable foreign keys
  db.pragma('foreign_keys = ON');
  
  // For development: check if we need to initialize the database
  const tableExists = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'").get();
  
  if (!tableExists) {{
    // Read and execute the schema file
    const schemaPath = path.join(process.cwd(), 'db', 'schema.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');
    
    // Split by semicolon to execute each statement separately
    schema.split(';').forEach(statement => {{
      if (statement.trim()) {{
        db.prepare(statement).run();
      }}
    }});
    
    console.log('Database initialized with schema');
  }}
}} catch (error) {{
  console.error('Database initialization error:', error);
}}

// Export the database instance
export default db;
"""
        
        db_js_path = os.path.join(lib_dir, "db.js")
        with open(db_js_path, "w", encoding="utf-8") as f:
            f.write(db_js_content)
        created_files.append("/lib/db.js")
        
        # Create db-queries.js - reusable queries
        queries_js_content = """// Database queries and utility functions
import db from './db';
"""

        # Add authentication related queries if needed
        if input.include_auth:
            queries_js_content += """
import bcrypt from 'bcryptjs';
import crypto from 'crypto';

// User-related queries
export const userQueries = {
  // Create a new user
  createUser: db.prepare(`
    INSERT INTO users (username, email, password, name, bio, avatar_url)
    VALUES (?, ?, ?, ?, ?, ?)
  `),
  
  // Get user by ID
  getUserById: db.prepare(`
    SELECT id, username, email, name, bio, avatar_url, is_admin, created_at, updated_at
    FROM users WHERE id = ?
  `),
  
  // Get user by email (for login)
  getUserByEmail: db.prepare(`
    SELECT id, username, email, password, name, bio, avatar_url, is_admin, created_at, updated_at
    FROM users WHERE email = ?
  `)
};

// Helper functions for auth
export function hashPassword(password) {
  return bcrypt.hashSync(password, 10);
}

export function verifyPassword(password, hashedPassword) {
  return bcrypt.compareSync(password, hashedPassword);
}

export function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}
"""

        # Add session related code if needed
        if input.include_session:
            # Also create session.js
            session_js_content = """// Iron session configuration
import { withIronSessionApiRoute, withIronSessionSsr } from 'iron-session/next';

const sessionOptions = {
  password: process.env.SESSION_PASSWORD || 'complex_password_at_least_32_characters_long',
  cookieName: 'blog_session',
  cookieOptions: {
    secure: process.env.NODE_ENV === 'production',
    maxAge: 60 * 60 * 24 * 7, // 1 week
  },
};

export function withSessionRoute(handler) {
  return withIronSessionApiRoute(handler, sessionOptions);
}

export function withSessionSsr(handler) {
  return withIronSessionSsr(handler, sessionOptions);
}
"""
            session_js_path = os.path.join(lib_dir, "session.js")
            with open(session_js_path, "w", encoding="utf-8") as f:
                f.write(session_js_content)
            created_files.append("/lib/session.js")

        # Add content query functions
        queries_js_content += """
// Post-related queries
export const postQueries = {
  // Create a new post
  createPost: db.prepare(`
    INSERT INTO posts (title, content, summary, slug, published, featured_image, author_id, category_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `),
  
  // Get all published posts
  getAllPublishedPosts: db.prepare(`
    SELECT p.*, 
           u.username as author_username, u.name as author_name, u.avatar_url as author_avatar,
           c.name as category_name, c.slug as category_slug,
           (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count
    FROM posts p
    JOIN users u ON p.author_id = u.id
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE p.published = 1
    ORDER BY p.created_at DESC
    LIMIT ? OFFSET ?
  `),
  
  // Get total count of published posts
  getPublishedPostCount: db.prepare(`
    SELECT COUNT(*) as count FROM posts WHERE published = 1
  `),
  
  // Get published post by slug
  getPostBySlug: db.prepare(`
    SELECT p.*, 
           u.username as author_username, u.name as author_name, u.avatar_url as author_avatar,
           c.name as category_name, c.slug as category_slug,
           (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count
    FROM posts p
    JOIN users u ON p.author_id = u.id
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE p.slug = ? AND (p.published = 1 OR p.author_id = ?)
  `)
};

// Helper functions
export function createSlug(title) {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}
"""
        
        queries_js_path = os.path.join(lib_dir, "db-queries.js")
        with open(queries_js_path, "w", encoding="utf-8") as f:
            f.write(queries_js_content)
        created_files.append("/lib/db-queries.js")
        
        # Create basic API route for posts
        api_dir = os.path.join(path_manager.project_path, "pages", "api")
        posts_dir = os.path.join(api_dir, "posts")
        os.makedirs(posts_dir, exist_ok=True)
        
        posts_index_content = """// API route for posts
import db from '../../../lib/db';
import { postQueries, createSlug } from '../../../lib/db-queries';

export default function handler(req, res) {
  // GET: Fetch posts with pagination
  if (req.method === 'GET') {
    const { page = 1, limit = 10 } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);
    
    try {
      const posts = postQueries.getAllPublishedPosts.all(limit, offset);
      
      // Get total count for pagination
      const totalCount = postQueries.getPublishedPostCount.get().count;
      
      return res.status(200).json({
        posts,
        pagination: {
          total: totalCount,
          page: parseInt(page),
          pageSize: parseInt(limit),
          totalPages: Math.ceil(totalCount / parseInt(limit))
        }
      });
    } catch (error) {
      console.error('Error fetching posts:', error);
      return res.status(500).json({ error: 'Failed to fetch posts' });
    }
  }
  
  // Method not allowed
  res.setHeader('Allow', ['GET']);
  return res.status(405).json({ error: `Method ${req.method} not allowed` });
}
"""
        
        posts_index_path = os.path.join(posts_dir, "index.js")
        with open(posts_index_path, "w", encoding="utf-8") as f:
            f.write(posts_index_content)
        created_files.append("/pages/api/posts/index.js")
        
        # Create .env.local with database configuration
        env_local_content = """# Database Configuration
DATABASE_PATH=./data/blog.db
SESSION_PASSWORD=complex_password_at_least_32_characters_long
"""
        env_local_path = os.path.join(path_manager.project_path, ".env.local")
        with open(env_local_path, "w", encoding="utf-8") as f:
            f.write(env_local_content)
        created_files.append("/.env.local")
        
        return SetupSQLiteOutput(
            success=True,
            message="SQLite successfully set up in the Next.js project",
            created_files=created_files
        )
    except Exception as e:
        return SetupSQLiteOutput(
            success=False,
            message=f"Failed to set up SQLite: {str(e)}",
            created_files=created_files
        )








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
    print(f"Reading page from {input.url}")
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
    print(f"Writing page to {input.url}")
    actual_path = path_manager.resolve_path(input.url)
    os.makedirs(os.path.dirname(actual_path), exist_ok=True)
    with open(actual_path, "w", encoding="utf-8") as f:
        f.write(input.content)
    return WritePageOutput(success=True, message=f"Page written successfully to {input.url}")

class ListPagesOutput(BaseModel):
    pages: List[str]  # List of virtual URLs

def list_all_pages() -> ListPagesOutput:
    print("List all pages called")
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
    print("Writing Cypress tests")
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
    print("Reading Cypress tests")
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






@code_generation_agent.tool
async def setup_sqlite_tool(ctx: RunContext[Dict[str, Any]], schema_content: str, 
                           include_auth: bool = True, include_session: bool = True,
                           database_name: str = "blog.db") -> str:
    """
    Set up a SQLite database in the Next.js project.
    
    Args:
        schema_content: The SQL schema content to initialize the database with tables
        include_auth: Whether to include authentication features (default: True)
        include_session: Whether to include session management (default: True)
        database_name: Name of the SQLite database file (default: "blog.db")
        
    Returns:
        A message describing the result of the setup process with a list of created files
    """
    # Create input model
    input_config = SetupSQLiteInput(
        schema_content=schema_content,
        include_auth=include_auth,
        include_session=include_session,
        database_name=database_name
    )
    
    # Call the function to set up SQLite
    result = setup_sqlite_database(input_config)
    
    if result.success:
        files_created = "\n- " + "\n- ".join(result.created_files)
        return f"SQLite database set up successfully. Created files: {files_created}"
    else:
        return f"Failed to set up SQLite database: {result.message}"




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
