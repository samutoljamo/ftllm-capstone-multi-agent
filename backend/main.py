from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime
import os
import uuid
import sys
from dotenv import load_dotenv; load_dotenv()

# Add agent module to path
from agent.main import full_development_flow
from agent.agents.context import CodeGenerationDeps

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProjectRequest(BaseModel):
    description: str

class ProjectResponse(BaseModel):
    project_id: str
    directory: str
    description: str  # Add description to response

# Store active WebSocket connections and project data
active_connections = {}
project_data_store = {}  # Store project data including descriptions

async def send_iteration_update(
    websocket: WebSocket,
    iteration_id: str,
    iteration_number: int,
    status: str,
    progress: int,
    details: str = None,
):
    """Send iteration status update through WebSocket"""
    await websocket.send_json({
        "type": "iteration_update",
        "iterationId": iteration_id,
        "iterationNumber": iteration_number,
        "status": status,
        "progress": progress,
        "details": details,
        "message": f"Iteration {iteration_number}: {status} - {progress}%",
        "timestamp": datetime.now().isoformat(),
    })

async def send_agent_update(
    websocket: WebSocket,
    iteration_id: str,
    agent_id: str,
    agent_name: str,
    status: str,
    progress: int,
    details: str = None,
):
    """Send agent status update through WebSocket"""
    await websocket.send_json({
        "type": "agent_update",
        "iterationId": iteration_id,
        "agentId": agent_id,
        "agentName": agent_name,
        "status": status,
        "progress": progress,
        "details": details,
        "message": f"Agent {agent_name}: {status} - {progress}%",
        "timestamp": datetime.now().isoformat(),
    })

async def send_tool_call(
    websocket: WebSocket,
    iteration_id: str,
    agent_id: str,
    tool_id: str,
    tool_name: str,
    status: str,
    details: str = None,
):
    """Send tool call update through WebSocket"""
    await websocket.send_json({
        "type": "tool_call",
        "iterationId": iteration_id,
        "agentId": agent_id,
        "toolId": tool_id,
        "toolName": tool_name,
        "status": status,
        "details": details,
        "message": f"Tool {tool_name}: {status}",
        "timestamp": datetime.now().isoformat(),
    })

class WebSocketNotifier:
    """Callback handler to send WebSocket notifications for the agent system"""
    def __init__(self, websocket, project_id):
        self.websocket = websocket
        self.project_id = project_id
        self.current_iteration = 0
        self.current_iteration_id = None
        
    async def start_iteration(self, iteration_number):
        """Start a new iteration and return the iteration ID"""
        self.current_iteration = iteration_number
        self.current_iteration_id = str(uuid.uuid4())
        
        await send_iteration_update(
            self.websocket,
            self.current_iteration_id,
            iteration_number,
            "in_progress",
            0,
            f"Starting iteration {iteration_number}"
        )
        
        return self.current_iteration_id
    
    async def complete_iteration(self):
        """Mark the current iteration as complete"""
        if self.current_iteration_id:
            await send_iteration_update(
                self.websocket,
                self.current_iteration_id,
                self.current_iteration,
                "completed",
                100,
                f"Iteration {self.current_iteration} completed successfully"
            )
    
    async def notify_agent_start(self, agent_name):
        """Notify that an agent has started"""
        agent_id = str(uuid.uuid4())
        
        await send_agent_update(
            self.websocket,
            self.current_iteration_id,
            agent_id,
            agent_name,
            "in_progress",
            0,
            f"Starting {agent_name}"
        )
        
        return agent_id
    
    async def notify_agent_complete(self, agent_id, agent_name):
        """Notify that an agent has completed"""
        await send_agent_update(
            self.websocket,
            self.current_iteration_id,
            agent_id,
            agent_name,
            "completed",
            100,
            f"{agent_name} completed"
        )
    
    async def notify_tool_call(self, agent_id, tool_id, tool_name, status, details=None):
        """Notify about a tool call"""
        await send_tool_call(
            self.websocket,
            self.current_iteration_id,
            agent_id,
            tool_id,
            tool_name,
            status,
            details
        )
        
        return tool_id

async def run_project_generation(websocket: WebSocket, project_data: dict):
    """Run actual project generation using agent package"""
    project_id = project_data["project_id"]
    directory = project_data["directory"]
    description = project_data.get("description", "Create a simple Next.js application")

    print(f"Running project generation for {project_id} in directory {directory}, description: {description}")
    
    # Create a notifier for callbacks
    notifier = WebSocketNotifier(websocket, project_id)
    
    try:
        # Run the development flow with the notifier
        result = await full_development_flow(
            project_description=description,
            max_iterations=3,
            notifier=notifier,
            project_directory=directory  # Pass the directory to use
        )
        
        # Send final message
        await websocket.send_json({
            "type": "completion",
            "projectId": project_id,
            "success": result.get("tests_passed", False),
            "message": "Project generation completed",
            "timestamp": datetime.now().isoformat(),
        })
    
    except Exception as e:
        print(f"Error in project generation: {e}")
        # Send error message
        await websocket.send_json({
            "type": "error",
            "projectId": project_id,
            "message": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        })

@app.post("/start-project", response_model=ProjectResponse)
async def start_project(request: ProjectRequest):
    """Start a new project generation"""
    project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    directory = f"generated_projects/{project_id}"
    
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Store project data including description
    project_data_store[project_id] = {
        "project_id": project_id,
        "directory": directory,
        "description": request.description
    }
    
    return ProjectResponse(
        project_id=project_id, 
        directory=directory,
        description=request.description
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    project_id = None
    
    try:
        # Receive project data
        initial_data = await websocket.receive_json()
        project_id = initial_data["project_id"]
        
        # Get stored project data including description
        project_data = project_data_store.get(project_id)
        if not project_data:
            raise ValueError(f"No project data found for ID: {project_id}")
        
        # Store connection
        active_connections[project_id] = websocket
        
        # Start actual project generation with stored description
        await run_project_generation(websocket, project_data)
        
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up connection and stored data
        if project_id:
            if project_id in active_connections:
                del active_connections[project_id]
            if project_id in project_data_store:
                del project_data_store[project_id]
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
