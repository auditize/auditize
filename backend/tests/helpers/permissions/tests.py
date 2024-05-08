from httpx import Response

from auditize.database import DatabaseManager

from ..apikeys import PreparedApikey
from ..database import assert_collection
from ..http import HttpTestHelper
from ..logs import UNKNOWN_OBJECT_ID
from ..repos import PreparedRepo
from ..users import PreparedUser


class BasePermissionTests:
    # workaround circular imports

    """
    Common tests related to permissions for users and apikeys.
    """

    @property
    def base_path(self):
        raise NotImplementedError()

    def get_principal_collection(self, dbm: DatabaseManager):
        raise NotImplementedError()

    async def inject_grantor(
        self, dbm: DatabaseManager, permissions=None
    ) -> PreparedUser | PreparedApikey:
        raise NotImplementedError()

    def prepare_assignee_data(self, permissions=None) -> dict:
        raise NotImplementedError()

    async def create_assignee(
        self, client: HttpTestHelper, dbm: DatabaseManager, data: dict = None
    ) -> PreparedUser | PreparedApikey:
        raise NotImplementedError()

    def rebuild_assignee_from_response(
        self, resp: Response, data: dict, dbm: DatabaseManager
    ) -> PreparedUser | PreparedApikey:
        raise NotImplementedError()

    async def test_create_custom_permissions(
        self, repo: PreparedRepo, dbm: DatabaseManager
    ):
        grantor = await self.inject_grantor(dbm, {"is_superadmin": True})
        assignee_data = self.prepare_assignee_data(
            {
                "permissions": {
                    "management": {"repos": {"read": True, "write": True}},
                    "logs": {"repos": {repo.id: {"read": True, "write": True}}},
                }
            }
        )
        async with grantor.client() as client:
            resp = await client.assert_post(
                self.base_path,
                json=assignee_data,
                expected_status_code=201,
            )

        assignee = self.rebuild_assignee_from_response(resp, assignee_data, dbm)
        await assert_collection(
            self.get_principal_collection(dbm),
            [
                assignee.expected_document(
                    {
                        "permissions": {
                            "is_superadmin": False,
                            "logs": {
                                "read": False,
                                "write": False,
                                "repos": {repo.id: {"read": True, "write": True}},
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
        await superadmin_client.assert_post(
            self.base_path,
            json=self.prepare_assignee_data(
                {
                    "permissions": {
                        "logs": {
                            "repos": {UNKNOWN_OBJECT_ID: {"read": True, "write": True}}
                        },
                    }
                }
            ),
            expected_status_code=400,
        )

    async def test_create_forbidden_permissions(self, dbm: DatabaseManager):
        grantor = await self.inject_grantor(
            dbm,
            {"management": {"users": {"write": True}, "apikeys": {"write": True}}},
        )

        async with grantor.client() as client:
            await client.assert_forbidden_post(
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
        dbm: DatabaseManager,
    ):
        grantor = await self.inject_grantor(dbm, {"is_superadmin": True})
        async with grantor.client() as client:
            assignee = await self.create_assignee(
                client,
                dbm,
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
                            "repos": {repo.id: {"read": True, "write": True}},
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
            self.get_principal_collection(dbm),
            [
                assignee.expected_document(
                    {
                        "permissions": {
                            "is_superadmin": False,
                            "logs": {
                                "read": False,
                                "write": False,
                                "repos": {repo.id: {"read": True, "write": True}},
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
        self, superadmin_client: HttpTestHelper, dbm: DatabaseManager
    ):
        assignee = await self.create_assignee(superadmin_client, dbm)
        await superadmin_client.assert_patch(
            f"{self.base_path}/{assignee.id}",
            json={
                "permissions": {
                    "logs": {
                        "repos": {UNKNOWN_OBJECT_ID: {"read": True, "write": True}},
                    },
                }
            },
            expected_status_code=400,
        )

    async def test_update_forbidden_permissions(self, dbm: DatabaseManager):
        grantor = await self.inject_grantor(
            dbm,
            {"management": {"users": {"write": True}, "apikeys": {"write": True}}},
        )

        async with grantor.client() as client:
            assignee = await self.create_assignee(client, dbm)
            await client.assert_forbidden_patch(
                f"{self.base_path}/{assignee.id}",
                json={
                    "permissions": {
                        "is_superadmin": True,
                    }
                },
            )
