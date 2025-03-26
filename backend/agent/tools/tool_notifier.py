"""
Tool notification wrapper module for sending tool usage updates to the frontend.
"""
import functools
from typing import Callable, Any
from pydantic_ai import RunContext
import uuid
import json

def get_tool_details(tool_name: str, args: tuple, kwargs: dict) -> str:
    """Generate detailed description of what the tool is doing based on its name and arguments"""
    
    if tool_name == "generate_sqlite_database":
        return kwargs.get("database_generation_instructions")
    
    try:
        # Extract the first argument after context which is typically the input model
        input_data = args[1] if len(args) > 1 else next(iter(kwargs.values()), None)
        
        # Base description just using tool name if we can't get more details
        base_description = f"Executing {tool_name}"
        
        if not input_data:
            return base_description

        # Convert input to dict if it's a Pydantic model
        if hasattr(input_data, "dict"):
            input_dict = input_data.dict()
        elif isinstance(input_data, dict):
            input_dict = input_data
        else:
            return base_description

        # Tool-specific detail formatting
        if tool_name == "read_file_content":
            target = input_dict.get('file_path')
            return f"Reading file{': ' + target if target else ''}"
            
        elif tool_name == "write_file":
            target = input_dict.get('file_path')
            return f"Writing to file{': ' + target if target else ''}"
            
        elif tool_name == "write_page":
            url = input_dict.get('url')
            return f"Creating page{' at: ' + url if url else ''}"
            
        elif tool_name == "read_page":
            url = input_dict.get('url')
            return f"Reading page{' at: ' + url if url else ''}"
            
        elif tool_name == "list_all_pages":
            return "Listing all available pages"
            
        elif tool_name == "create_directory":
            path = input_dict.get('directory_path')
            return f"Creating directory{': ' + path if path else ''}"

        elif tool_name == "write_cypress_tests":
            return "Writing Cypress test cases"
            
        elif tool_name == "read_cypress_tests":
            return "Reading Cypress test cases"
        
        return base_description
        
    except Exception as e:
        return f"Executing {tool_name} (error getting details: {str(e)})"

async def notify_tool_call(notifier, agent_id, tool_id, tool_name, status, details=None):
    """Notify about a tool call if notifier is available"""
    if notifier:
        await notifier.notify_tool_call(
            agent_id=agent_id,
            tool_id=tool_id,
            tool_name=tool_name,
            status=status,
            details=details
        )

def tool_notifier(func: Callable) -> Callable:
    """
    Decorator that wraps a tool's inner function to send notifications about its usage.
    This wrapper is meant to be used on the function that gets passed to the Tool class.
    
    Args:
        func: The inner tool function to wrap (the one that gets passed to Tool class)
        
    Returns:
        A wrapped function that sends notifications and then calls the original function
    """
    @functools.wraps(func)
    async def wrapper(ctx: RunContext, *args, **kwargs) -> Any:
        # Extract deps from context
        deps = getattr(ctx, "deps", None)
        
        # Only proceed with notification if we have deps with notifier and agent info
        notifier = getattr(deps, "notifier", None) if deps else None
        agent_id = getattr(deps, "agent_id", None) if deps else None
            
        if notifier and agent_id:
            # Extract tool name from function name
            tool_name = func.__name__.lstrip("_")  # Remove leading underscore from internal function names
            
            # Generate a single tool_id for this tool call
            tool_id = str(uuid.uuid4())
            
            # Get detailed description of what the tool is doing
            tool_details = get_tool_details(tool_name, args, kwargs)
            start_details = tool_details if tool_details else f"Starting {tool_name}"
            
            # Notify about tool call starting
            await notify_tool_call(
                notifier=notifier,
                agent_id=agent_id,
                tool_id=tool_id,
                tool_name=tool_name,
                status="in_progress",
                details=start_details
            )
            
            try:
                # Call the original function
                result = await func(ctx, *args, **kwargs)
                
                # Notify about tool call completion
                complete_details = f"Completed: {tool_details}" if tool_details else f"Completed {tool_name}"
                await notify_tool_call(
                    notifier=notifier,
                    agent_id=agent_id,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    status="completed",
                    details=complete_details
                )
                
                return result
                
            except Exception as e:
                # Notify about tool call failure
                error_details = f"Error in {tool_details if tool_details else tool_name}: {str(e)}"
                await notify_tool_call(
                    notifier=notifier,
                    agent_id=agent_id,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    status="failed",
                    details=error_details
                )
                raise
        else:
            print("No notifier or agent id")
            # Just call the original function without notification
            return await func(ctx, *args, **kwargs)
            
    return wrapper 