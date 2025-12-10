import uuid

import callee

from auditize.database.dbm import open_db_session
from auditize.log_i18n_profile.models import LogI18nProfileCreate
from auditize.log_i18n_profile.service import create_log_i18n_profile

from .utils import DATETIME_FORMAT


class PreparedLogI18nProfile:
    EMPTY_TRANSLATION = {
        "action_type": {},
        "action_category": {},
        "actor_type": {},
        "actor_extra_field_name": {},
        "actor_extra_field_value_enum": {},
        "source_field_name": {},
        "source_field_value_enum": {},
        "detail_field_name": {},
        "detail_field_value_enum": {},
        "resource_type": {},
        "resource_extra_field_name": {},
        "resource_extra_field_value_enum": {},
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
        "actor_extra_field_name": {
            "actor_custom_field_1": "actor_custom_field_1 EN",
        },
        "actor_extra_field_value_enum": {
            "actor_custom_field_1": {
                "enum_value_1": "actor_custom_field_enum_value_1 EN",
            }
        },
        "source_field_name": {
            "source_field_1": "source_field_1 EN",
        },
        "source_field_value_enum": {
            "source_field_1": {
                "enum_value_1": "source_field_enum_value_1 EN",
            }
        },
        "detail_field_name": {
            "detail_field_1": "detail_field_1 EN",
        },
        "detail_field_value_enum": {
            "detail_field_1": {
                "enum_value_1": "detail_field_enum_value_1 EN",
            }
        },
        "resource_type": {
            "resource_type_1": "resource_type_1 EN",
        },
        "resource_extra_field_name": {
            "resource_custom_field_1": "resource_custom_field_1 EN",
        },
        "resource_extra_field_value_enum": {
            "resource_custom_field_1": {
                "enum_value_1": "resource_custom_field_enum_value_1 EN",
            }
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
        "actor_extra_field_name": {
            "actor_custom_field_1": "actor_custom_field_1 FR",
        },
        "actor_extra_field_value_enum": {
            "actor_custom_field_1": {
                "enum_value_1": "actor_custom_field_enum_value_1 FR",
            }
        },
        "source_field_name": {
            "source_field_1": "source_field_1 FR",
        },
        "source_field_value_enum": {
            "source_field_1": {
                "enum_value_1": "source_field_enum_value_1 FR",
            }
        },
        "detail_field_name": {
            "detail_field_1": "detail_field_1 FR",
        },
        "detail_field_value_enum": {
            "detail_field_1": {
                "enum_value_1": "detail_field_enum_value_1 FR",
            }
        },
        "resource_type": {
            "resource_type_1": "resource_type_1 FR",
        },
        "resource_extra_field_name": {
            "resource_custom_field_1": "resource_custom_field_1 FR",
        },
        "resource_extra_field_value_enum": {
            "resource_custom_field_1": {
                "enum_value_1": "resource_custom_field_enum_value_1 FR",
            }
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
    async def create(cls, data=None):
        if not data:
            data = cls.prepare_data()
        async with open_db_session() as session:
            profile = await create_log_i18n_profile(
                session, LogI18nProfileCreate(**data)
            )
        return cls(str(profile.id), data)

    @classmethod
    def build_expected_api_response(cls, extra=None):
        if extra is None:
            extra = {}
        return {
            "id": callee.IsA(str),
            "created_at": DATETIME_FORMAT,
            "updated_at": DATETIME_FORMAT,
            **extra,
            "translations": {
                lang: {**cls.EMPTY_TRANSLATION, **translation}
                for lang, translation in extra.get("translations", {}).items()
            },
        }

    def expected_api_response(self, extra=None) -> dict:
        return self.build_expected_api_response(
            {
                "id": self.id,
                "name": self.data["name"],
                "translations": self.data.get("translations", {}),
                **(extra or {}),
            }
        )
