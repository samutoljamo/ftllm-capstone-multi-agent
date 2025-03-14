from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
import os

class ReadPageInput(BaseModel):
    url: str  # Virtual URL, e.g., "/index.js"

class ReadPageOutput(BaseModel):
    content: str

def _read_page(ctx: RunContext, input: ReadPageInput) -> ReadPageOutput:
    print(f"Reading page from {input.url}")
    actual_path = os.path.join(ctx.deps.project_path, input.url)
    try:
        with open(actual_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ReadPageOutput(content=content)
    except FileNotFoundError:
        return ReadPageOutput(content="")
    
read_page = Tool(_read_page)

