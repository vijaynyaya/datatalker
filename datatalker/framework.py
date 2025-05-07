from typing import AsyncGenerator, Union

from datatalker.context import set_context
from datatalker.types import (
    Context,
    Message, MessageRole
)

class DataTalker:
    """
    DataTalker provides a natural language interface for data.

    Envisioned Capabilites:
    - Chat: General conversation and assistance
    - Retrieval: Finding and loading datasets
    - Data Analysis: Analyzing and visualizing data
    - Reasoning: Explaining insights and patterns
    - Tools: Excuting specific functions such as data transformation
    """
    def __init__(self):
        self.ctx = Context()
        self.num_hops = 5
        set_context(self.ctx)
        # register tools and handlers
        self.current_handler = None
        # self.chat_handler
        # self.reasoning_handler
        # self.retrieval_handler
        # self.data_handler
        # self.viz_handler
        # self.triage_handler
        # self.tool_handler


    def handle_message(self, message: str) -> Union[Message, AsyncGenerator]:
        """Main entry point for handling messages"""
        usr_msg = Message(role=MessageRole.USER, content=message)
        self.ctx.add_message(usr_msg)

        for i in range(self.num_hops):
            resp, next_handler = self.current_handler.handle()
            yield resp
            if next_handler is not None:
                self.current_handler = next_handler
            if i == (self.num_hops - 1):
                self.current_handler = self.chat_handler
                print("Reached hop limit. Stopping...")

                
