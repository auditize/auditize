import asyncio
import io
import uuid
from contextlib import contextmanager
from unittest import mock

import pytest
from pydantic_ai import (
    ModelResponse,
    TextPart,
    ToolCallPart,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)
from pydantic_ai.messages import ModelMessage, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from auditize.__main__ import async_main
from auditize.config import get_config
from auditize.database.dbm import open_db_session
from auditize.exceptions import PermissionDenied
from auditize.llm_tools.service import ToolLogService
from auditize.llm_tools.tools import LOG_TOOLS
from auditize.log_analysis.agent import _build_model, analyze_logs
from auditize.log_analysis.tools import get_tools
from auditize.repo.service import get_repo
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


class ScriptedModel:
    """
    Plays a list of model turns, each turn being the list of parts of a model response
    (text or tool calls), and records the parts sent back to the model.
    """

    def __init__(self, *turns: list[TextPart | ToolCallPart]):
        self.turns = iter(turns)
        self.received_parts = []

    def _next_turn(self, messages: list[ModelMessage]) -> list[TextPart | ToolCallPart]:
        self.received_parts.extend(messages[-1].parts)
        return next(self.turns)

    async def _function(
        self, messages: list[ModelMessage], _: AgentInfo
    ) -> ModelResponse:
        return ModelResponse(parts=self._next_turn(messages))

    @property
    def model(self) -> FunctionModel:
        return FunctionModel(self._function)

    def get_tool_returns(self, tool_name: str) -> list:
        return [
            part.content
            for part in self.received_parts
            if isinstance(part, ToolReturnPart) and part.tool_name == tool_name
        ]


@contextmanager
def _mock_model(scripted_model: ScriptedModel):
    with mock.patch(
        "auditize.log_analysis.agent._build_model",
        return_value=scripted_model.model,
    ):
        yield


async def _run_analysis_cli(repo_id: str, prompt: str):
    with mock.patch("sys.stdin", io.StringIO(prompt)):
        await async_main(["analyze-logs", repo_id])


async def test_analysis_cli(
    superadmin_client: HttpTestHelper, repo: PreparedRepo, capsys
):
    await repo.create_log(superadmin_client)
    model = ScriptedModel(
        [ToolCallPart("count_logs", {"search_params": {}})],
        [TextPart("There is 1 log")],
    )

    with _mock_model(model):
        await _run_analysis_cli(repo.id, "How many logs?")

    assert model.get_tool_returns("count_logs") == [1]
    assert capsys.readouterr().out == "There is 1 log\n"


async def test_analysis_cli_tool_calls_do_not_overlap(repo: PreparedRepo, capsys):
    # tools share the same database session, which does not support concurrent
    # operations
    running = 0
    max_running = 0

    async def count_logs(**_):
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        await asyncio.sleep(0.01)
        running -= 1
        return 1

    model = ScriptedModel(
        [
            ToolCallPart("count_logs", {"search_params": {}}),
            ToolCallPart("count_logs", {"search_params": {}}),
        ],
        [TextPart("Done")],
    )

    with _mock_model(model):
        with mock.patch.object(ToolLogService, "count_logs", side_effect=count_logs):
            await _run_analysis_cli(repo.id, "How many logs?")

    assert model.get_tool_returns("count_logs") == [1, 1]
    assert max_running == 1
    assert capsys.readouterr().out == "Done\n"


async def test_analysis_cli_tool_error_sent_to_model(repo: PreparedRepo, capsys):
    model = ScriptedModel(
        [ToolCallPart("describe_action", {"action_type": "unknown"})],
        [TextPart("This action type does not exist")],
    )

    with _mock_model(model):
        await _run_analysis_cli(repo.id, "Describe the action type")

    tool_returns = model.get_tool_returns("describe_action")
    assert len(tool_returns) == 1
    assert "Unknown action type 'unknown'" in tool_returns[0]
    assert capsys.readouterr().out == "This action type does not exist\n"


async def test_analysis_cli_model_error(repo: PreparedRepo):
    # the model calls a tool in loop, until the maximum number of retries is reached
    model = ScriptedModel(
        *[
            [ToolCallPart("describe_action", {"action_type": "unknown"})]
            for _ in range(10)
        ],
    )

    with _mock_model(model):
        with pytest.raises(UnexpectedModelBehavior, match="exceeded max retries"):
            await _run_analysis_cli(repo.id, "Describe the action type")


async def test_analysis_cli_output_tokens_limit(repo: PreparedRepo):
    model = ScriptedModel([TextPart("word " * 10_001)])

    with _mock_model(model):
        with pytest.raises(UsageLimitExceeded, match="output_tokens_limit of 10000"):
            await _run_analysis_cli(repo.id, "How many logs?")


async def test_analysis_cli_llm_not_configured(repo: PreparedRepo):
    with pytest.raises(SystemExit) as exc_info:
        await _run_analysis_cli(repo.id, "How many logs?")

    assert "LLM is not configured" in str(exc_info.value.code)


async def test_analysis_cli_empty_prompt(repo: PreparedRepo):
    with pytest.raises(SystemExit) as exc_info:
        await _run_analysis_cli(repo.id, " \n")

    assert "prompt" in str(exc_info.value.code)


async def test_analysis_cli_unknown_repo():
    unknown_repo_id = str(uuid.uuid4())
    with mock.patch("sys.stdin") as stdin:
        with pytest.raises(SystemExit) as exc_info:
            await async_main(["analyze-logs", unknown_repo_id])

    assert exc_info.value.code == f"Error: repository {unknown_repo_id} not found"
    stdin.read.assert_not_called()


async def test_analysis_cli_disabled_repo(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.update_status(superadmin_client, "disabled")

    with mock.patch("sys.stdin") as stdin:
        with pytest.raises(PermissionDenied):
            await async_main(["analyze-logs", repo.id])

    stdin.read.assert_not_called()


async def test_analyze_logs(superadmin_client: HttpTestHelper, repo: PreparedRepo):
    await repo.create_log(superadmin_client)
    model = ScriptedModel(
        [
            TextPart("Let me count"),
            ToolCallPart("count_logs", {"search_params": {}}),
        ],
        [TextPart("There is 1 log")],
    )

    with _mock_model(model):
        async with open_db_session() as session:
            output = await analyze_logs(
                session, await get_repo(session, repo.id), "How many logs?"
            )

    assert model.get_tool_returns("count_logs") == [1]
    assert output == "There is 1 log"
