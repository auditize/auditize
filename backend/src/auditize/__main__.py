import argparse
import asyncio
import getpass
import json
import sys

from auditize.app import build_api_app
from auditize.config import get_config, init_config
from auditize.database import init_dbm
from auditize.exceptions import ConfigError, ConstraintViolation
from auditize.openapi import get_customized_openapi_schema
from auditize.permissions.models import Permissions
from auditize.scheduler import build_scheduler
from auditize.user.models import User
from auditize.user.service import (
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


async def _bootstrap_superadmin(
    email: str, first_name: str, last_name: str, password: str
):
    await save_user(
        User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hash_user_password(password),
            permissions=Permissions(is_superadmin=True),
        ),
    )


async def bootstrap_superadmin(email: str, first_name: str, last_name: str):
    password = _get_password()

    try:
        await _bootstrap_superadmin(email, first_name, last_name, password)
    except ConstraintViolation:
        sys.exit(f"Error: user with email {email} already exists")
    print(f"User with email {email} has been successfully created")


async def bootstrap_default_superadmin():
    users, _ = await get_users(query=None, page=1, page_size=1)
    if not users:
        await _bootstrap_superadmin(
            "super.admin@example.net", "Super", "Admin", "auditize"
        )


async def schedule():
    scheduler = build_scheduler()
    scheduler.start()
    try:
        while True:
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        scheduler.shutdown()


async def dump_config():
    config = get_config()
    print(json.dumps(config.to_dict(), ensure_ascii=False, indent=4))


async def dump_openapi():
    print(
        json.dumps(
            get_customized_openapi_schema(
                build_api_app(), include_internal_routes=False
            ),
            ensure_ascii=False,
            indent=4,
        )
    )


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

    # CMD schedule
    schedule_parser = sub_parsers.add_parser("schedule")
    schedule_parser.set_defaults(func=lambda _: schedule())

    # CMD config
    config_parser = sub_parsers.add_parser("config")
    config_parser.set_defaults(func=lambda _: dump_config())

    # CMD openapi
    openapi_parser = sub_parsers.add_parser("openapi")
    openapi_parser.set_defaults(func=lambda _: dump_openapi())

    parsed_args = parser.parse_args(args)
    await parsed_args.func(parsed_args)

    return 0


if __name__ == "__main__":
    try:
        init_config()
    except ConfigError as exc:
        sys.exit("ERROR: " + str(exc))

    init_dbm()

    sys.exit(asyncio.run(main(sys.argv[1:])))
