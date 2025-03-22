from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from typing import List
import os

class ListPagesOutput(BaseModel):
    pages: List[str]  # List of virtual URLs

def _list_all_pages(ctx: RunContext) -> ListPagesOutput:
    print("List all pages called")
    project_path = ctx.deps.project_path
    
    pages_dir = os.path.join(project_path, "pages")
    pages = []
    if os.path.exists(pages_dir):
        for root, _, files in os.walk(pages_dir):
            for file in files:
                if file.endswith(".js") or file.endswith(".tsx") or file.endswith(".jsx"):
                    actual_path = os.path.join(root, file)
                    # Convert to virtual URL
                    relative_path = os.path.relpath(actual_path, pages_dir)
                    virtual_url = f"/{relative_path}"
                    pages.append(virtual_url)
    print(pages)
    return ListPagesOutput(pages=pages)

list_all_pages = Tool(_list_all_pages)
