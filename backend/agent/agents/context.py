from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CodeGenerationDeps(BaseModel):
    project_description: str
    feedback: Optional[str] = None
    project_path: str
    ai_model_name: str
    feedback_message: Optional[str] = None
    agent_name: Optional[str] = None
    agent_id: Optional[str] = None
    notifier: Optional[Any] = None

class CypressTestsDeps(BaseModel):  
    project_path: str
    action: str = "generate_tests"

class FeedbackDeps(BaseModel):
    test_output: str
    test_errors: List[str]
    server_output: Optional[Dict[str, str]] = None

class FeedbackOutput(BaseModel):
    feedback_message: str

# Define output types for tools
class ListPagesOutput(BaseModel):
    pages: List[str]  # List of virtual URLs

class ReadPageOutput(BaseModel):
    content: str  # Content of the page
    exists: bool  # Whether the page exists

class WritePageOutput(BaseModel):
    success: bool  # Whether the write operation was successful
    message: str  # Success or error message

class CypressTestsOutput(BaseModel):
    success: bool  # Whether the operation was successful
    message: str  # Success or error message

# =======================
# Data Models for SQLite Agent
# =======================

class SQLiteConfigOutput(BaseModel):
    """Output from SQLite agent"""
    success: bool  # Whether the operation was successful
    message: str  # Success or error message
    api_documentation: str # Documentation for the API routes