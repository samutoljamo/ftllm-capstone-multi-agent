from pydantic import BaseModel
from typing import List, Optional, Dict
from pydantic_ai.models.openai import OpenAIModel

class CodeGenerationDeps(BaseModel):
    project_description: str
    feedback: Optional[str] = None
    project_path: str
    ai_model_name: str
    feedback_message: Optional[str] = None

class CypressTestsDeps(BaseModel):  
    project_path: str
    action: str = "generate_tests"

class FeedbackDeps(BaseModel):
    test_output: str
    test_errors: List[str]
    server_output: Optional[Dict[str, str]] = None

class FeedbackOutput(BaseModel):
    feedback_message: str



# =======================
# Data Models for SQLite Agent
# =======================



class SQLiteConfigOutput(BaseModel):
    """Output from SQLite agent"""
    success: bool  # Whether the operation was successful
    message: str  # Success or error message
    api_documentation: str # Documentation for the API routes