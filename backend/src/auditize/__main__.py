import argparse
import asyncio
import sys

from auditize.database import get_dbm
from auditize.log.service import apply_log_retention_period
from auditize.permissions.models import Permissions
from auditize.user.models import User
from auditize.user.service import get_users, hash_user_password, save_user


async def bootstrap_default_superadmin():
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
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers()
    bootstrap_default_superadmin_parser = sub_parsers.add_parser(
        "bootstrap-default-superadmin"
    )
    bootstrap_default_superadmin_parser.set_defaults(func=bootstrap_default_superadmin)
    purge_expired_logs_parser = sub_parsers.add_parser("purge-expired-logs")
    purge_expired_logs_parser.set_defaults(func=purge_expired_logs)

    args = parser.parse_args(args)
    await args.func()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
