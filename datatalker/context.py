from datatalker.types import Context

_CONTEXT: Context | None = None

def get_context() -> Context:
    if _CONTEXT is None:
        raise RuntimeError("No active Context.")
    
def set_context(ctx: Context) -> None:
    _CONTEXT = ctx
    print("Updated conversation context.")