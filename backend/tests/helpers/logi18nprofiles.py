import uuid
from datetime import datetime

import callee

from auditize.database import DatabaseManager
from auditize.logi18nprofiles.models import LogI18nProfile
from auditize.logi18nprofiles.service import create_log_i18n_profile


class PreparedLogI18nProfile:
    EMPTY_TRANSLATION = {
        "action_type": {},
        "action_category": {},
        "actor_type": {},
        "actor_custom_field": {},
        "source_field": {},
        "detail_field": {},
        "resource_type": {},
        "resource_custom_field": {},
        "tag_type": {},
        "attachment_type": {},
    }
    ENGLISH_TRANSLATION = {
        "action_type": {
            "action_type_1": "action_type_1 EN",
        },
        "action_category": {
            "action_1": "action_1 EN",
        },
        "actor_type": {
            "actor_type_1": "actor_type_1 EN",
        },
        "actor_custom_field": {
            "actor_custom_field_1": "actor_custom_field_1 EN",
        },
        "source_field": {
            "source_field_1": "source_field_1 EN",
        },
        "detail_field": {
            "detail_field_1": "detail_field_1 EN",
        },
        "resource_type": {
            "resource_type_1": "resource_type_1 EN",
        },
        "resource_custom_field": {
            "resource_custom_field_1": "resource_custom_field_1 EN",
        },
        "tag_type": {
            "tag_type_1": "tag_type_1 EN",
        },
        "attachment_type": {
            "attachment_type_1": "attachment_type_1 EN",
        },
    }
    FRENCH_TRANSLATION = {
        "action_type": {
            "action_type_1": "action_type_1 FR",
        },
        "action_category": {
            "action_1": "action_1 FR",
        },
        "actor_type": {
            "actor_type_1": "actor_type_1 FR",
        },
        "actor_custom_field": {
            "actor_custom_field_1": "actor_custom_field_1 FR",
        },
        "source_field": {
            "source_field_1": "source_field_1 FR",
        },
        "detail_field": {
            "detail_field_1": "detail_field_1 FR",
        },
        "resource_type": {
            "resource_type_1": "resource_type_1 FR",
        },
        "resource_custom_field": {
            "resource_custom_field_1": "resource_custom_field_1 FR",
        },
        "tag_type": {
            "tag_type_1": "tag_type_1 FR",
        },
        "attachment_type": {
            "attachment_type_1": "attachment_type_1 FR",
        },
    }

    def __init__(self, id: str, data: dict):
        self.id = id
        self.data = data

    @staticmethod
    def prepare_data(extra=None):
        return {"name": f"i18n profile {uuid.uuid4()}", **(extra or {})}

    @classmethod
    async def create(cls, dbm: DatabaseManager, data=None):
        if not data:
            data = cls.prepare_data()
        profile_id = await create_log_i18n_profile(dbm, LogI18nProfile(**data))
        return cls(profile_id, data)

    def expected_document(self, extra=None):
        return {
            "_id": uuid.UUID(self.id),
            "created_at": callee.IsA(datetime),
            "name": self.data["name"],
            "translations": {
                lang: {**self.EMPTY_TRANSLATION, **translation}
                for lang, translation in self.data.get("translations", {}).items()
            },
            **(extra or {}),
        }

    def expected_api_response(self, extra=None) -> dict:
        return {
            "id": self.id,
            "created_at": callee.IsA(str),
            "name": self.data["name"],
            "translations": self.data.get("translations", {}),
            **(extra or {}),
        }
