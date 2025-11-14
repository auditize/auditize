import uuid

import callee

from .log import UNKNOWN_UUID
from .utils import DATETIME_FORMAT

DEFAULT_SEARCH_PARAMETERS = {
    "action_category": None,
    "action_type": None,
    "actor_name": None,
    "actor_ref": None,
    "actor_type": None,
    "has_attachment": None,
    "attachment_mime_type": None,
    "attachment_name": None,
    "attachment_type": None,
    "entity_ref": None,
    "resource_name": None,
    "resource_ref": None,
    "resource_type": None,
    "since": None,
    "tag_name": None,
    "tag_ref": None,
    "tag_type": None,
    "until": None,
    "q": None,
}


class PreparedLogFilter:
    def __init__(self, id: str | None, data: dict):
        self.id = id
        self.data = data

    @staticmethod
    def prepare_data(extra=None):
        return {
            "name": f"Filter {uuid.uuid4()}",
            "repo_id": UNKNOWN_UUID,
            "search_params": {"action_type": "some action"},
            "columns": ["saved_at", "action_type"],
            **(extra or {}),
        }

    def expected_api_response(self, extra=None) -> dict:
        if extra is None:
            extra = {}
        search_params = extra.get("search_params", self.data.get("search_params", {}))
        return {
            "id": self.id if self.id else callee.IsA(str),
            "name": self.data["name"],
            "created_at": DATETIME_FORMAT,
            "updated_at": DATETIME_FORMAT,
            "repo_id": self.data["repo_id"],
            "columns": self.data["columns"],
            "is_favorite": self.data.get("is_favorite", False),
            **(extra or {}),
            "search_params": {
                **DEFAULT_SEARCH_PARAMETERS,
                **search_params,
            },
        }
