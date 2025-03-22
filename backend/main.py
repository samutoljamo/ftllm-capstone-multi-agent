from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import Dict, List, Callable, Awaitable
from pydantic import BaseModel
import os
import uuid

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class ProjectRequest(BaseModel):
    project_name: str
    description: str

class ProjectResponse(BaseModel):
    project_id: str
    project_name: str
    description: str
    status: str
    directory: str

@app.post("/start-project")
async def start_project(request: ProjectRequest):
    """Start a new Next.js project generation"""
    project_id = str(uuid.uuid4())
    project_dir = f"generated_projects/{project_id}"
    
    return {
        "status": "started",
        "project_id": project_id,
        "project_name": request.project_name,
        "description": request.description,
        "directory": project_dir
    }

async def simulated_project_generation(log: Callable[[str], Awaitable[None]], project_name: str, project_dir: str):
    """Simulated Next.js project generation workflow"""
    await log("Starting Next.js project generation...")
    await asyncio.sleep(1)
    
    await log(f"Creating project directory: {project_name}")
    await asyncio.sleep(1)
    
    await log("Initializing Next.js project with TypeScript...")
    await asyncio.sleep(2)
    
    await log("Installing dependencies...")
    await asyncio.sleep(2)
    
    await log("Setting up project structure...")
    await asyncio.sleep(1)
    
    await log("Configuring TypeScript...")
    await asyncio.sleep(1)
    
    await log("Setting up Tailwind CSS...")
    await asyncio.sleep(1)
    
    await log("Creating initial pages...")
    await asyncio.sleep(1)
    
    await log("Project generation completed!")
    await log(f"To start the project, run: cd {project_dir} && npm run dev")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Create a logging function that sends messages through the websocket
        async def log_message(message: str):
            await websocket.send_json({
                "message": message
            })
        
        # Receive project details
        data = await websocket.receive_json()
        project_name = data.get("project_name")
        project_dir = data.get("directory")
        
        # Start the project generation
        await simulated_project_generation(log_message, project_name, project_dir)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await log_message(f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
