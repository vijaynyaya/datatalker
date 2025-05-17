"""
Handlers can access the context directly to call tools. 
"""
from datatalker.context import get_context

class Handler:
    def __init__(self):
        self.ctx = get_context()