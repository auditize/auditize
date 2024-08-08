import uuid
from datetime import datetime

import callee

from .log import UNKNOWN_UUID

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
    "node_ref": None,
    "resource_name": None,
    "resource_ref": None,
    "resource_type": None,
    "since": None,
    "tag_name": None,
    "tag_ref": None,
    "tag_type": None,
    "until": None,
}


class PreparedLogFilter:
    def __init__(self, id: str, data: dict):
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

    def expected_document(self, extra=None):
        repo_id = (
            extra["repo_id"] if extra and "repo_id" in extra else self.data["repo_id"]
        )
        return {
            "_id": uuid.UUID(self.id),
            "name": self.data["name"],
            "created_at": callee.IsA(datetime),
            "search_params": {
                **DEFAULT_SEARCH_PARAMETERS,
                **self.data["search_params"],
                "since": (
                    datetime.fromisoformat(self.data["search_params"]["since"])
                    if "since" in self.data["search_params"]
                    else None
                ),
                "until": (
                    datetime.fromisoformat(self.data["search_params"]["until"])
                    if "until" in self.data["search_params"]
                    else None
                ),
            },
            "columns": self.data["columns"],
            **(extra or {}),
            "repo_id": uuid.UUID(repo_id),
        }

    def expected_api_response(self, extra=None) -> dict:
        return {
            "id": self.id,
            "name": self.data["name"],
            "created_at": callee.IsA(str),
            "repo_id": self.data["repo_id"],
            "search_params": {
                **DEFAULT_SEARCH_PARAMETERS,
                **self.data["search_params"],
            },
            "columns": self.data["columns"],
            **(extra or {}),
        }
