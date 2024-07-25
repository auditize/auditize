import asyncio
import sys

from auditize.database import get_dbm
from auditize.logs.service import apply_log_retention_period
from auditize.permissions.models import Permissions
from auditize.users.models import User
from auditize.users.service import get_users, hash_user_password, save_user


async def bootstrap_superadmin():
    dbm = get_dbm()
    users, _ = await get_users(dbm, query=None, page=1, page_size=1)
    if len(users) > 0:
        return
    await save_user(
        dbm,
        User(
            first_name="Super",
            last_name="Admin",
            email="super.admin@example.net",
            password_hash=hash_user_password("auditize"),
            permissions=Permissions(is_superadmin=True),
        ),
    )


async def purge_expired_logs():
    await apply_log_retention_period(get_dbm())


async def main(args):
    if args[0] == "bootstrap_superadmin":
        await bootstrap_superadmin()
    elif args[0] == "purge_expired_logs":
        await purge_expired_logs()
    else:
        print("Usage: python -m auditize CMD", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
