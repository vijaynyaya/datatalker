from datatalker.types import Context

CONTEXT: Context | None = None

def get_context() -> Context:
    if CONTEXT is None:
        raise RuntimeError("No active Context.")
    
def set_context(ctx: Context) -> None:
    CONTEXT = ctx
    print("Updated conversation context.")