import functools
import inspect
import uuid
from collections.abc import Awaitable, Callable, Iterator

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.tools import Tool
from mcp.types import ToolAnnotations
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.auth.authorizer import (
    Authenticated,
    authenticate_apikey,
    get_bearer_token_from_authorization_header,
)
from auditize.database.dbm import open_db_session
from auditize.exceptions import AuditizeException, InternalError
from auditize.llm_tools.service import ToolContext, ToolLogService
from auditize.llm_tools.tools import LOG_TOOLS
from auditize.logger import get_logger
from auditize.permissions.assertions import can_read_logs_from_repo

logger = get_logger(__name__)

_TOOL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,  # Only internal data
)


async def get_authorized(
    db_session: AsyncSession = Depends(open_db_session),
) -> Authenticated:
    headers = get_http_headers(include_all=True)

    authorization_header = headers.get("authorization")
    if not authorization_header:
        raise ToolError("Authorization header is required")

    bearer_token = get_bearer_token_from_authorization_header(authorization_header)
    authenticated = await authenticate_apikey(db_session, bearer_token)

    return authenticated


async def get_log_service(
    db_session: AsyncSession = Depends(open_db_session),
    authenticated: Authenticated = Depends(get_authorized),
) -> ToolLogService:
    headers = get_http_headers()

    raw_repo_id = headers.get("x-auditize-repo")
    if not raw_repo_id:
        raise ToolError("X-Auditize-Repo header is required")

    try:
        repo_id = uuid.UUID(raw_repo_id)
    except ValueError:
        raise ToolError(f"Invalid X-Auditize-Repo header {raw_repo_id!r}")

    if not authenticated.comply(can_read_logs_from_repo(repo_id)):
        raise ToolError(
            f"Apikey does not have permission to read logs from repository {repo_id!r}"
        )

    return await ToolLogService.for_reading(db_session, repo_id)


def get_authorized_entities(
    log_service: ToolLogService = Depends(get_log_service),
    authorized: Authenticated = Depends(get_authorized),
) -> set[str]:
    return authorized.permissions.get_repo_readable_entities(log_service.repo.id)


async def get_tool_context(
    log_service: ToolLogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> ToolContext:
    return ToolContext(log_service=log_service, authorized_entities=authorized_entities)


def to_mcp_tool(fn: Callable[..., Awaitable]) -> Tool:
    """
    Turn a tool function taking a ToolContext as first parameter into a FastMCP tool,
    the ToolContext being provided by the get_tool_context dependency.
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

    @functools.wraps(fn)
    async def wrapper(**kwargs):
        ctx = kwargs.pop(ctx_param.name)
        try:
            return await fn(ctx, **kwargs)
        except Exception as exc:
            if isinstance(exc, AuditizeException) and not isinstance(
                exc, InternalError
            ):
                raise ToolError(str(exc)) from None
            logger.exception("An unexpected error occurred")
            raise ToolError("Internal Error") from exc

    # FastMCP builds the tool input schema from the signature: the context parameter
    # is moved at the end as keyword-only (since it has a default value) and
    # its Depends() default makes FastMCP inject it and hide it from the schema.
    wrapper.__signature__ = sig.replace(
        parameters=[
            *tool_params,
            ctx_param.replace(
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=Depends(get_tool_context),
            ),
        ]
    )
    return Tool.from_function(wrapper, annotations=_TOOL_ANNOTATIONS)


def get_tools() -> Iterator[Tool]:
    yield from map(to_mcp_tool, LOG_TOOLS)
