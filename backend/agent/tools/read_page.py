from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
import os
from .tool_notifier import tool_notifier

class ReadPageInput(BaseModel):
    url: str  # Virtual URL, e.g., "/index.js"

class ReadPageOutput(BaseModel):
    content: str

def _read_page(ctx: RunContext, input: ReadPageInput) -> ReadPageOutput:
    if(input.url.startswith("/")):
        input.url = input.url[1:]
    actual_path = os.path.join(ctx.deps.project_path, "pages", input.url)
    try:
        # check if the file exists
        if not os.path.exists(actual_path):
            return ReadPageOutput(content="PATH NOT FOUND")
        # check if the file is a directory
        if os.path.isdir(actual_path):
            return ReadPageOutput(content="PATH IS A DIRECTORY")
        with open(actual_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ReadPageOutput(content=content)
    except FileNotFoundError:
        return ReadPageOutput(content="")
    
read_page = Tool(tool_notifier(_read_page))

