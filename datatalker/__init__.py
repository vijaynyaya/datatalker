from datatalker.router import Router
import streamlit as st


class Context:
    def __init__(self, state=dict()):
        self.state = state
    
    def get(self, key: str):
        return self.state.get(key)
    
    def set(self, key: str, value):
        self.state[key] = value
        return self.state


class DataTalker:
    def __init__(self, router: Router):
        self.router = router
        self.context = Context(dict())
        self.context.set("resources", [])
        self.logger = st.write
    
    def respond(self, message: str):
        return self.router.dispatch(message, context=self.context, logger=self.logger)