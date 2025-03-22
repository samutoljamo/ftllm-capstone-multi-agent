from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime
import os
import uuid

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
    project_name: str
    description: str

class ProjectResponse(BaseModel):
    project_id: str
    directory: str

# Store active WebSocket connections
active_connections: dict[str, WebSocket] = {}

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

async def send_nested_agent_update(
    websocket: WebSocket,
    iteration_id: str,
    parent_agent_id: str,
    agent_id: str,
    agent_name: str,
    status: str,
    progress: int,
    details: str = None,
):
    """Send nested agent status update through WebSocket"""
    await websocket.send_json({
        "type": "nested_agent_update",
        "iterationId": iteration_id,
        "parentAgentId": parent_agent_id,
        "agentId": agent_id,
        "agentName": agent_name,
        "status": status,
        "progress": progress,
        "details": details,
        "message": f"Nested Agent {agent_name}: {status} - {progress}%",
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

async def simulate_project_generation(websocket: WebSocket, project_data: dict):
    """Simulate project generation with multiple iterations"""
    project_id = project_data["project_id"]
    directory = project_data["directory"]

    # Simulate 3 iterations
    for iteration_number in range(1, 4):
        iteration_id = str(uuid.uuid4())
        
        try:
            # Start iteration
            await send_iteration_update(
                websocket,
                iteration_id,
                iteration_number,
                "in_progress",
                0,
                f"Starting iteration {iteration_number}",
            )

            # Code generation agent
            code_agent_id = str(uuid.uuid4())
            await send_agent_update(
                websocket,
                iteration_id,
                code_agent_id,
                "Code Generation Agent",
                "in_progress",
                0,
                f"Setting up code generation for iteration {iteration_number}",
            )

            # Tool calls for code generation
            await send_tool_call(
                websocket,
                iteration_id,
                code_agent_id,
                f"{code_agent_id}-tool-1",
                "list_pages",
                "in_progress",
            )
            await asyncio.sleep(2)
            await send_tool_call(
                websocket,
                iteration_id,
                code_agent_id,
                f"{code_agent_id}-tool-1",
                "list_pages",
                "completed",
                f"Retrieved list of pages for iteration {iteration_number}",
            )

            await send_tool_call(
                websocket,
                iteration_id,
                code_agent_id,
                f"{code_agent_id}-tool-2",
                "read_page",
                "in_progress",
            )
            await asyncio.sleep(2)
            await send_tool_call(
                websocket,
                iteration_id,
                code_agent_id,
                f"{code_agent_id}-tool-2",
                "read_page",
                "completed",
                f"Read page content for iteration {iteration_number}",
            )

            await send_tool_call(
                websocket,
                iteration_id,
                code_agent_id,
                f"{code_agent_id}-tool-3",
                "write_page",
                "in_progress",
            )
            await asyncio.sleep(2)
            await send_tool_call(
                websocket,
                iteration_id,
                code_agent_id,
                f"{code_agent_id}-tool-3",
                "write_page",
                "completed",
                f"Generated new page for iteration {iteration_number}",
            )

            await send_agent_update(
                websocket,
                iteration_id,
                code_agent_id,
                "Code Generation Agent",
                "completed",
                100,
                f"Code generation completed for iteration {iteration_number}",
            )

            # DB agent
            db_agent_id = str(uuid.uuid4())
            await send_agent_update(
                websocket,
                iteration_id,
                db_agent_id,
                "DB Agent",
                "in_progress",
                0,
                f"Setting up database operations for iteration {iteration_number}",
            )

            # Tool calls for DB operations
            await send_tool_call(
                websocket,
                iteration_id,
                db_agent_id,
                f"{db_agent_id}-tool-1",
                "list_pages",
                "in_progress",
            )
            await asyncio.sleep(2)
            await send_tool_call(
                websocket,
                iteration_id,
                db_agent_id,
                f"{db_agent_id}-tool-1",
                "list_pages",
                "completed",
                f"Retrieved pages from database for iteration {iteration_number}",
            )

            await send_tool_call(
                websocket,
                iteration_id,
                db_agent_id,
                f"{db_agent_id}-tool-2",
                "read_page",
                "in_progress",
            )
            await asyncio.sleep(2)
            await send_tool_call(
                websocket,
                iteration_id,
                db_agent_id,
                f"{db_agent_id}-tool-2",
                "read_page",
                "completed",
                f"Read page from database for iteration {iteration_number}",
            )

            await send_agent_update(
                websocket,
                iteration_id,
                db_agent_id,
                "DB Agent",
                "completed",
                100,
                f"Database operations completed for iteration {iteration_number}",
            )

            # Iteration completion
            await send_iteration_update(
                websocket,
                iteration_id,
                iteration_number,
                "completed",
                100,
                f"Iteration {iteration_number} completed successfully",
            )

            # Wait between iterations
            if iteration_number < 3:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error in iteration {iteration_number}: {e}")
            await websocket.close()
            return

@app.post("/start-project", response_model=ProjectResponse)
async def start_project(request: ProjectRequest):
    """Start a new project generation"""
    project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    directory = f"generated_projects/{project_id}"
    
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    return ProjectResponse(project_id=project_id, directory=directory)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        # Receive project data
        project_data = await websocket.receive_json()
        project_id = project_data["project_id"]
        
        # Store connection
        active_connections[project_id] = websocket
        
        # Start project generation
        await simulate_project_generation(websocket, project_data)
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
    finally:
        # Clean up connection
        if project_id in active_connections:
            del active_connections[project_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
