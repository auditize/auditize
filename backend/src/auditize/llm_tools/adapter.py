import inspect
from collections.abc import Awaitable, Callable

from auditize.exceptions import AuditizeException, InternalError
from auditize.llm_tools.service import ToolContext


def split_tool_signature(
    fn: Callable[..., Awaitable],
) -> tuple[inspect.Signature, inspect.Parameter, list[inspect.Parameter]]:
    """
    Validate a tool function and return its signature, its context parameter and its
    other parameters.
    """
    if not inspect.iscoroutinefunction(fn):
        raise TypeError(f"Tool {fn.__name__!r} must be an async function")

    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    if not params or params[0].annotation is not ToolContext:
        raise TypeError(
            f"First parameter of tool {fn.__name__!r} must be annotated as ToolContext"
        )
    ctx_param, *tool_params = params
    return sig, ctx_param, tool_params


def is_tool_usage_error(exc: Exception) -> bool:
    """
    Tell whether an exception raised by a tool function is caused by the way the tool
    has been called, and can then be reported to its caller.
    """
    return isinstance(exc, AuditizeException) and not isinstance(exc, InternalError)
