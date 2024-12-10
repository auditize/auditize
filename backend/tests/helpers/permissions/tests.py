from uuid import UUID

import callee
from httpx import Response

from conftest import RepoBuilder

from ..apikey import PreparedApikey
from ..database import assert_collection
from ..http import HttpTestHelper
from ..log import UNKNOWN_UUID
from ..repo import PreparedRepo
from ..user import PreparedUser


class BasePermissionTests:
    # workaround circular imports

    """
    Common tests related to permissions for users and apikeys.
    """

    @property
    def base_path(self):
        raise NotImplementedError()

    def get_principal_collection(self):
        raise NotImplementedError()

    async def inject_grantor(self, permissions=None) -> PreparedUser | PreparedApikey:
        raise NotImplementedError()

    def prepare_assignee_data(self, permissions=None) -> dict:
        raise NotImplementedError()

    async def create_assignee(
        self, client: HttpTestHelper, data: dict = None
    ) -> PreparedUser | PreparedApikey:
        raise NotImplementedError()

    def rebuild_assignee_from_response(
        self, resp: Response, data: dict
    ) -> PreparedUser | PreparedApikey:
        raise NotImplementedError()

    async def test_create_custom_permissions(self, repo_builder: RepoBuilder):
        repo_1 = await repo_builder({})
        repo_2 = await repo_builder({})

        grantor = await self.inject_grantor({"is_superadmin": True})
        assignee_data = self.prepare_assignee_data(
            {
                "permissions": {
                    "management": {"repos": {"read": True, "write": True}},
                    "logs": {
                        "repos": [
                            {"repo_id": repo_1.id, "read": True, "write": True},
                            {
                                "repo_id": repo_2.id,
                                "readable_entities": ["customer:1"],
                            },
                        ],
                    },
                }
            }
        )
        async with grantor.client() as client:
            resp = await client.assert_post(
                self.base_path,
                json=assignee_data,
                expected_status_code=201,
            )

        assignee = self.rebuild_assignee_from_response(resp, assignee_data)
        await assert_collection(
            self.get_principal_collection(),
            [
                assignee.expected_document(
                    {
                        "permissions": {
                            "is_superadmin": False,
                            "logs": {
                                "read": False,
                                "write": False,
                                "repos": [
                                    {
                                        "repo_id": UUID(repo_1.id),
                                        "read": True,
                                        "write": True,
                                        "readable_entities": [],
                                    },
                                    {
                                        "repo_id": UUID(repo_2.id),
                                        "read": False,
                                        "write": False,
                                        "readable_entities": ["customer:1"],
                                    },
                                ],
                            },
                            "management": {
                                "repos": {"read": True, "write": True},
                                "users": {"read": False, "write": False},
                                "apikeys": {"read": False, "write": False},
                            },
                        }
                    }
                )
            ],
        )

    async def test_create_custom_permissions_unknown_repo(
        self,
        superadmin_client: HttpTestHelper,
    ):
        await superadmin_client.assert_post_bad_request(
            self.base_path,
            json=self.prepare_assignee_data(
                {
                    "permissions": {
                        "logs": {
                            "repos": [
                                {
                                    "repo_id": UNKNOWN_UUID,
                                    "read": True,
                                    "write": True,
                                }
                            ]
                        },
                    }
                }
            ),
            expected_json={
                "message": callee.Contains("cannot be assigned in log permissions"),
                "localized_message": None,
                "validation_errors": [],
            },
        )

    async def test_create_forbidden_permissions(self):
        grantor = await self.inject_grantor(
            {"management": {"users": {"write": True}, "apikeys": {"write": True}}},
        )

        async with grantor.client() as client:
            await client.assert_post_forbidden(
                self.base_path,
                json=self.prepare_assignee_data(
                    {
                        "permissions": {
                            "is_superadmin": True,
                        }
                    }
                ),
            )

    async def test_update_permissions(
        self,
        repo: PreparedRepo,
    ):
        grantor = await self.inject_grantor({"is_superadmin": True})
        async with grantor.client() as client:
            assignee = await self.create_assignee(
                client,
                self.prepare_assignee_data(
                    {
                        "permissions": {
                            "logs": {"read": True, "write": False},
                            "management": {
                                "repos": {"read": True, "write": True},
                            },
                        }
                    }
                ),
            )

            await client.assert_patch(
                f"{self.base_path}/{assignee.id}",
                json={
                    "permissions": {
                        "logs": {
                            "read": False,
                            "write": False,
                            "repos": [
                                {
                                    "repo_id": repo.id,
                                    "read": False,
                                    "write": True,
                                    "readable_entities": ["entity1"],
                                }
                            ],
                        },
                        "management": {
                            "repos": {"read": False, "write": False},
                            "users": {"read": True, "write": True},
                        },
                    }
                },
                expected_status_code=204,
            )

        await assert_collection(
            self.get_principal_collection(),
            [
                assignee.expected_document(
                    {
                        "permissions": {
                            "is_superadmin": False,
                            "logs": {
                                "read": False,
                                "write": False,
                                "repos": [
                                    {
                                        "repo_id": UUID(repo.id),
                                        "read": False,
                                        "write": True,
                                        "readable_entities": ["entity1"],
                                    }
                                ],
                            },
                            "management": {
                                "repos": {"read": False, "write": False},
                                "users": {"read": True, "write": True},
                                "apikeys": {"read": False, "write": False},
                            },
                        }
                    }
                )
            ],
        )

    async def test_update_permissions_unknown_repo(
        self, superadmin_client: HttpTestHelper
    ):
        assignee = await self.create_assignee(superadmin_client)
        await superadmin_client.assert_patch_bad_request(
            f"{self.base_path}/{assignee.id}",
            json={
                "permissions": {
                    "logs": {
                        "repos": [
                            {"repo_id": UNKNOWN_UUID, "read": True, "write": True}
                        ],
                    },
                }
            },
            expected_json={
                "message": callee.Contains("cannot be assigned in log permissions"),
                "localized_message": None,
                "validation_errors": [],
            },
        )

    async def test_update_permissions_unknown_repo_in_existing_permissions(
        self,
        superadmin_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        assignee = await self.create_assignee(
            superadmin_client,
            self.prepare_assignee_data(
                {
                    "logs": {
                        "repos": [
                            {"repo_id": repo.id, "read": True, "write": True},
                        ]
                    }
                }
            ),
        )
        await superadmin_client.assert_delete_no_content(f"/repos/{repo.id}")
        await superadmin_client.assert_patch_no_content(
            f"{self.base_path}/{assignee.id}",
            json={"permissions": {"management": {"repos": {"write": True}}}},
        )

    async def test_update_forbidden_permissions(self):
        grantor = await self.inject_grantor(
            {"management": {"users": {"write": True}, "apikeys": {"write": True}}},
        )

        async with grantor.client() as client:
            assignee = await self.create_assignee(client)
            await client.assert_patch_forbidden(
                f"{self.base_path}/{assignee.id}",
                json={
                    "permissions": {
                        "is_superadmin": True,
                    }
                },
            )
