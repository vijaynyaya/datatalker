from datatalker.context import get_context
from datatalker.types import SystemLog, Thought
import dspy

MAX_RECORDS = 32000

class SelectResource(dspy.Signature):
    """Select one resource"""
    resources: list = dspy.InputField(desc="List of resources to choose from")
    message: str = dspy.InputField(desc="User or system message to guide selection")
    resource_index: int = dspy.InputField(desc="Index of the selected resource")


def resource_selector(instruction: str = None):
    """Selects a resource from context"""
    ctx = get_context()
    if len(ctx.resources) == 0:
        return SystemLog("No datasets are in context. Use resource retrieval.")
    
    rsrcs = list(ctx.resources.values())
    selector = dspy.ChainOfThought(SelectResource)
    selection = selector(
        resources=[
            {
                "title": doc["metadatas"]["title"],
                "description": doc["long_text"] 
            }
            for doc in rsrcs
        ],
        message=instruction
    )
    rsrc = rsrcs[selection.resource_index]
    return rsrc


def data_loading_handler():
    ctx = get_context()
    rsrc = resource_selector(ctx.user_message)
    # TODO: check if the selected resource is already loaded.

    
