"""
Tool notification wrapper module for sending tool usage updates to the frontend.
"""
import functools
from typing import Callable, Any
from pydantic_ai import RunContext

async def notify_tool_call(notifier, agent_id, tool_name, status, details=None):
    """Notify about a tool call if notifier is available"""
    if notifier:
        await notifier.notify_tool_call(
            agent_id=agent_id,
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
            
            # Notify about tool call starting
            await notify_tool_call(
                notifier=notifier,
                agent_id=agent_id,
                tool_name=tool_name,
                status="in_progress",
                details=f"Starting {tool_name}"
            )
            
            try:
                # Call the original function
                result = await func(ctx, *args, **kwargs)
                
                # Notify about tool call completion
                await notify_tool_call(
                    notifier=notifier,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    status="completed",
                    details=f"Completed {tool_name}"
                )
                
                return result
                
            except Exception as e:
                # Notify about tool call failure
                await notify_tool_call(
                    notifier=notifier,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    status="failed",
                    details=f"Error in {tool_name}: {str(e)}"
                )
                raise
        else:
            # Just call the original function without notification
            return await func(ctx, *args, **kwargs)
            
    return wrapper 