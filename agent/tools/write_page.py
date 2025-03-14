from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import Optional
import os

class WritePageInput(BaseModel):
    url: str    # Virtual URL
    content: str

class WritePageOutput(BaseModel):
    success: bool
    message: Optional[str] = None

def _write_page(ctx: RunContext, input: WritePageInput) -> WritePageOutput:
    print(ctx.deps)
    print(f"Writing page to {input.url}")
    actual_path = os.path.join(ctx.deps.project_path, input.url)
    print(f"Actual path: {actual_path}")
    os.makedirs(os.path.dirname(actual_path), exist_ok=True)
    with open(actual_path, "w", encoding="utf-8") as f:
        f.write(input.content)
    return WritePageOutput(success=True, message=f"Page written successfully to {input.url}")
    
write_page = Tool(_write_page)

