import functools
import inspect
from collections.abc import Awaitable, Callable, Iterator

from pydantic_ai import ModelRetry, RunContext, Tool

from auditize.llm_tools.adapter import is_tool_usage_error, split_tool_signature
from auditize.llm_tools.service import ToolContext
from auditize.llm_tools.tools import LOG_TOOLS

_TOOL_MAX_RETRIES = 3


def to_pydantic_ai_tool(fn: Callable[..., Awaitable]) -> Tool[ToolContext]:
    """
    Turn a tool function taking a ToolContext as first parameter into a Pydantic AI tool,
    the ToolContext being provided as the dependencies of the agent run.
    """
    sig, ctx_param, tool_params = split_tool_signature(fn)

    @functools.wraps(fn)
    async def wrapper(run_ctx: RunContext[ToolContext], **kwargs):
        try:
            return await fn(run_ctx.deps, **kwargs)
        except Exception as exc:
            if is_tool_usage_error(exc):
                # Let the model see the error so that it can fix its tool call
                raise ModelRetry(str(exc)) from None
            raise

    # Pydantic AI builds the tool input schema from the signature: with takes_ctx=True,
    # it skips the first parameter, which must not be annotated as anything else than
    # a RunContext.
    wrapper.__signature__ = sig.replace(
        parameters=[
            ctx_param.replace(annotation=inspect.Parameter.empty),
            *tool_params,
        ]
    )
    return Tool(
        wrapper,
        takes_ctx=True,
        max_retries=_TOOL_MAX_RETRIES,
        # Tools of an agent run share the same database session, which does not
        # support concurrent operations.
        sequential=True,
    )


def get_tools() -> Iterator[Tool[ToolContext]]:
    yield from map(to_pydantic_ai_tool, LOG_TOOLS)
