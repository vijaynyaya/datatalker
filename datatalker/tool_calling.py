# AgentType(enum): chat | retrieval | data | reasoning | tool
# HandoffStrategy(enum): keyword | intent | threshold | combined

# Intent: detected through NLP (example: keyword based approach)
# Agent:
#   .__init__(handler, handoffs, instructions)
#   .handle(message, history, context) -> response, next_agent // calls the handler and determines handoff

# ToolRegistery:
#   .register_tool(name, func, description)
#   .determine_input_kwargs(instruction: str, tool_name: str) -> dict
#   .execute(tool_name, **kwargs)

from typing import Callable
import dspy
import inspect

class GetFunctionKwargs(dspy.Signature):
    instruction: str = dspy.InputField("a detailled natural language instruction")
    python_function_usage_doc: str = dspy.InputField("docstring of the function")
    kwargs: dict[str, str] = dspy.OutputField("Keyword arguments for the function")

class ToolWrapper:
    def __init__(self, name: str, func: Callable, desciption: str):
        self.name = name
        self.function = func
        self.description = desciption
        self.usage = inspect.getdoc(func)
        self.kwargs_parser = dspy.ChainOfThought(GetFunctionKwargs)
    
    def invoke(self, instruction: str):
        kwargs = self.get_kwargs(instruction)
        return self.function(**kwargs)
    
    def get_kwargs(self, instruction: str):
        prediction = self.kwargs_parser(
            instruction=instruction,
            python_function_usage_doc=self.usage
        )
        return  prediction.kwargs