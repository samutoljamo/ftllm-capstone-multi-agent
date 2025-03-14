from pydantic import BaseModel
from typing import List, Optional

class CodeGenerationDeps(BaseModel):
    project_description: str
    feedback: Optional[str] = None
    project_path: str

class CypressTestsDeps(BaseModel):
    project_path: str
    action: str = "generate_tests"

class FeedbackDeps(BaseModel):
    test_output: str
    test_errors: List[str]

class FeedbackOutput(BaseModel):
    feedback_message: str
    suggestions: Optional[List[str]] = None