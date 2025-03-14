import os
import json
import subprocess
import time
import signal
from typing import Dict, Any, List, Optional

def install_packages(project_path: str) -> Dict[str, Any]:
    """
    Installs NPM packages for the Next.js project.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        A dictionary with success status, output, and errors.
    """
    if not project_path or not os.path.exists(project_path):
        raise ValueError(f"Invalid project path: {project_path}")
    
    print("Installing NPM packages...")
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300  # Timeout after 5 minutes
        )
        
        success = result.returncode == 0
        
        return {
            "success": success,
            "output": result.stdout,
            "errors": [result.stderr] if result.stderr else []
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Package installation timed out",
            "errors": ["NPM install timed out after 300 seconds"]
        }
    except subprocess.SubprocessError as e:
        return {
            "success": False,
            "output": "",
            "errors": [f"Error installing packages: {str(e)}"]
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": [f"Unexpected error during package installation: {str(e)}"]
        }

def start_nextjs_server(project_path: str) -> Dict[str, Any]:
    """
    Starts the Next.js development server.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        A dictionary with server process information, PID, and status.
    """
    if not project_path or not os.path.exists(project_path):
        raise ValueError(f"Invalid project path: {project_path}")
    
    print("Starting Next.js development server...")
    try:
        # Start the Next.js dev server as a background process
        server_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid  # Creates a new process group for easier termination later
        )
        
        # Give the server some time to start
        time.sleep(10)
        
        # Check if the process is still running
        if server_process.poll() is None:
            return {
                "success": True,
                "pid": server_process.pid,
                "process_group": os.getpgid(server_process.pid),
                "message": "Next.js server started successfully"
            }
        else:
            stderr = server_process.stderr.read()
            return {
                "success": False,
                "output": "",
                "errors": [f"Server process exited prematurely: {stderr}"]
            }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": [f"Unexpected error starting Next.js server: {str(e)}"]
        }

def stop_server(process_info: Dict[str, Any]) -> None:
    """
    Stops a running Next.js server.
    
    Args:
        process_info: Process information dictionary from start_nextjs_server
    """
    if process_info and process_info.get("success") and process_info.get("process_group"):
        try:
            os.killpg(process_info["process_group"], signal.SIGTERM)
            print("Next.js server stopped")
        except Exception as e:
            print(f"Error stopping server: {str(e)}")

def run_cypress_tests(project_path: str) -> Dict[str, Any]:
    """
    Prepares the environment and runs Cypress tests for a Next.js project.
    This function:
    1. Installs required NPM packages
    2. Starts the Next.js development server
    3. Runs Cypress tests
    4. Stops the server
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        A dictionary with success status, output, and errors.
    """
    if not project_path or not os.path.exists(project_path):
        raise ValueError(f"Invalid project path: {project_path}")
    
    # Check for test file and create proper directory structure if needed
    cypress_e2e_dir = os.path.join(project_path, "cypress", "e2e")
    cypress_integration_dir = os.path.join(project_path, "cypress", "integration")
    
    # Make sure e2e directory exists (for newer Cypress versions)
    os.makedirs(cypress_e2e_dir, exist_ok=True)
    
    # Find test file in either location
    test_file_paths = [
        os.path.join(cypress_e2e_dir, "app.cy.js"),
        os.path.join(cypress_integration_dir, "tests.spec.js")
    ]
    
    test_file_exists = any(os.path.exists(path) for path in test_file_paths)
    if not test_file_exists:
        return {
            "success": False,
            "output": "",
            "errors": ["No test file found. Please generate Cypress tests first."]
        }
    
    # Step 1: Install packages
    install_result = install_packages(project_path)
    if not install_result["success"]:
        return {
            "success": False,
            "output": install_result["output"],
            "errors": install_result["errors"] + ["Failed to install required packages"]
        }
    
    # Step 2: Start the Next.js server
    server_process = None
    try:
        server_info = start_nextjs_server(project_path)
        if not server_info["success"]:
            return {
                "success": False,
                "output": "",
                "errors": server_info.get("errors", ["Failed to start Next.js server"])
            }

        # Step 3: Run Cypress tests
        print("Running Cypress tests...")
        result = subprocess.run(
            ["npx", "cypress", "run", "--headless"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120  # Timeout after 2 minutes
        )
        
        # Process the result
        success = result.returncode == 0
        
        return {
            "success": success,
            "output": result.stdout,
            "errors": [result.stderr] if result.stderr and not success else []
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Test execution timed out",
            "errors": ["Cypress test execution timed out after 120 seconds"]
        }
    except subprocess.SubprocessError as e:
        return {
            "success": False,
            "output": "",
            "errors": [f"Error running Cypress tests: {str(e)}"]
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": [f"Unexpected error: {str(e)}"]
        }
    finally:
        # Step 4: Stop the Next.js server
        if server_info and server_info.get("success"):
            stop_server(server_info)