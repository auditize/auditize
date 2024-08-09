import argparse
import asyncio
import getpass
import sys

from auditize.database import get_dbm
from auditize.exceptions import UnknownModelException
from auditize.log.service import apply_log_retention_period
from auditize.permissions.models import Permissions
from auditize.user.models import User
from auditize.user.service import (
    get_user_by_email,
    get_users,
    hash_user_password,
    save_user,
)


def _get_password() -> str:
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match, please try again.", file=sys.stderr)
        print("", file=sys.stderr)
        return _get_password()

    return password


async def bootstrap_superadmin(email: str, first_name: str, last_name: str):
    dbm = get_dbm()

    password = _get_password()

    try:
        await get_user_by_email(dbm, email)
    except UnknownModelException:
        pass
    else:
        sys.exit(f"Error: user with email {email} already exists")

    await save_user(
        dbm,
        User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hash_user_password(password),
            permissions=Permissions(is_superadmin=True),
        ),
    )
    print(f"User with email {email} has been successfully created")


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
    sub_parsers = parser.add_subparsers(required=True)

    # CMD bootstrap-default-superadmin
    bootstrap_default_superadmin_parser = sub_parsers.add_parser(
        "bootstrap-default-superadmin"
    )
    bootstrap_default_superadmin_parser.set_defaults(
        func=lambda _: bootstrap_default_superadmin()
    )

    # CMD bootstrap-superadmin
    bootstrap_superadmin_parser = sub_parsers.add_parser("bootstrap-superadmin")
    bootstrap_superadmin_parser.add_argument("email")
    bootstrap_superadmin_parser.add_argument("first_name")
    bootstrap_superadmin_parser.add_argument("last_name")
    bootstrap_superadmin_parser.set_defaults(
        func=lambda cmd_args: bootstrap_superadmin(
            cmd_args.email, cmd_args.first_name, cmd_args.last_name
        )
    )

    # CMD purge-expired
    purge_expired_logs_parser = sub_parsers.add_parser("purge-expired-logs")
    purge_expired_logs_parser.set_defaults(func=lambda _: purge_expired_logs())

    parsed_args = parser.parse_args(args)
    await parsed_args.func(parsed_args)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
