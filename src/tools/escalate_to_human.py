


from typing import Any, Dict

from langchain.tools import tool

@tool
async def escalate_to_human(issue: Dict[str, Any]) -> str:
    """Escalate an issue to a human and return a confirmation message.
    
    Args:
        issue (Dict[str, Any]): A dictionary containing details about the issue to escalate.
        
    Returns:
        str: A confirmation message indicating that the issue has been escalated.
    """

    return f"The issue has been escalated to a human for further assistance. Details: {issue}"