from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Optional
import os
from .tool_notifier import tool_notifier
class WritePageInput(BaseModel):
    url: str    # Virtual URL
    content: str

class WritePageOutput(BaseModel):
    success: bool
    message: Optional[str] = None

def _write_page(ctx: RunContext, input: WritePageInput) -> WritePageOutput:
    if(input.url.startswith("/")):
        input.url = input.url[1:]
    print(f"Writing page to {input.url}")
    actual_path = os.path.join(ctx.deps.project_path, "pages", input.url)
    os.makedirs(os.path.dirname(actual_path), exist_ok=True)
    with open(actual_path, "w", encoding="utf-8") as f:
        f.write(input.content)
    return WritePageOutput(success=True, message=f"Page written successfully to {input.url}")
    
write_page = Tool(tool_notifier(_write_page))

