from datatalker.routes import router


class Context:
    def __init__(self, state=dict()):
        self.state = state
    
    def get(self, key: str):
        return self.state.get(key)
    
    def set(self, key: str, value):
        self.state[key] = value
        return self.state


class DataTalker:
    def __init__(self):
        self.router = router
        self.context = Context(dict())
        self.context.set("resources", [])
        self.logger = print
    
    def respond(self, message: str, history):
        return self.router.dispatch(message, context=self.context, logger=self.logger)