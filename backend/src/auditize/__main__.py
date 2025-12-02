import argparse
import asyncio
import getpass
import json
import platform
import sys
from uuid import UUID

import uvicorn
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from auditize.app import build_api_app, build_app
from auditize.config import get_config, init_config
from auditize.database import init_dbm
from auditize.database.dbm import migrate_database, open_db_session
from auditize.exceptions import (
    ConfigAlreadyInitialized,
    ConfigError,
    ConstraintViolation,
)
from auditize.log.index import get_reindexable_repos, is_index_up_to_date, reindex_index
from auditize.log.service import LogService
from auditize.openapi import get_customized_openapi_schema
from auditize.permissions.sql_models import Permissions
from auditize.repo.service import get_all_repos, get_repo
from auditize.scheduler import build_scheduler
from auditize.user.models import USER_PASSWORD_MIN_LENGTH
from auditize.user.service import (
    hash_user_password,
    save_user,
)
from auditize.user.sql_models import User
from auditize.version import __version__


def _lazy_init(*, skip_db_init=False):
    try:
        init_config()
    except ConfigAlreadyInitialized:
        # this case corresponds to tests where config and db are already initialized
        return
    except ConfigError as exc:
        sys.exit("ERROR: " + str(exc))

    if not skip_db_init:
        init_dbm()


def _get_password() -> str:
    password = getpass.getpass("Password: ")
    if len(password) < USER_PASSWORD_MIN_LENGTH:
        print(
            f"Password too short, it must be at least {USER_PASSWORD_MIN_LENGTH} characters long.",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        return _get_password()

    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match, please try again.", file=sys.stderr)
        print("", file=sys.stderr)
        return _get_password()

    return password


def _ask_confirm(message: str) -> bool:
    confirm = input(f"{message} [y/N]: ")
    return confirm.lower() == "y"


async def bootstrap_superadmin(email: str, first_name: str, last_name: str):
    _lazy_init()

    # Make sure we can connect to the database before asking for the password
    async with open_db_session() as session:
        try:
            await session.execute(text("SELECT 1"))
        except OperationalError as exc:
            sys.exit(f"Error: could not connect to the PostgreSQL database: {exc}")

    password = _get_password()

    try:
        async with open_db_session() as session:
            await save_user(
                session,
                User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password_hash=hash_user_password(password),
                    permissions=Permissions(is_superadmin=True),
                ),
            )
    except ConstraintViolation:
        # FIXME: we could get a ConstraintViolation for other reasons
        sys.exit(f"Error: user with email {email} already exists")
    print(f"User with email {email} has been successfully created")


async def serve(host: str, port: int):
    _lazy_init()
    app = build_app()
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)
    await server.serve()


async def purge_expired_logs(repo: UUID = None):
    _lazy_init()
    async with open_db_session() as session:
        await LogService.apply_log_retention_period(session, repo)


async def empty_repo(repo: UUID):
    _lazy_init()
    async with open_db_session() as session:
        log_service = await LogService.for_maintenance(session, repo)
        await log_service.empty_log_db()


async def reindex_repo(repo: UUID | None):
    _lazy_init()
    async with open_db_session() as session:
        if repo:
            repo = await get_repo(session, repo)
            if await is_index_up_to_date(repo):
                print(f"Repository {repo.id} index is already up to date")
                return
            if not _ask_confirm(
                f"Are you sure you want to reindex repository {repo.id}?"
            ):
                return
            repos = [repo]
        else:
            repos = await get_reindexable_repos(session)
            if not repos:
                print("All repositories are already up to date")
                return
            repos_as_str = "\n".join([f"- {repo.id} ({repo.name})" for repo in repos])
            if not _ask_confirm(
                f"The following repositories will be reindexed:\n{repos_as_str}"
                "\nAre you sure you want to continue?"
            ):
                return
        try:
            for repo in repos:
                await reindex_index(session, repo)
                print()
        except (KeyboardInterrupt, asyncio.CancelledError):
            print(
                "\nReindex operation has been interrupted by user, "
                "it can be resumed using the same command."
            )
            return


async def schedule():
    _lazy_init()
    scheduler = build_scheduler()
    scheduler.start()
    print("Scheduler started")
    try:
        while True:
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        scheduler.shutdown()


async def dump_config():
    _lazy_init(skip_db_init=True)
    config = get_config()
    print(json.dumps(config.to_dict(), ensure_ascii=False, indent=4))


async def dump_openapi():
    print(
        json.dumps(
            get_customized_openapi_schema(
                build_api_app(cors_allow_origins=[], online_doc=False),
                include_internal_routes=False,
            ),
            ensure_ascii=False,
            indent=4,
        )
    )


async def migrate_db():
    _lazy_init()
    await migrate_database()


async def version():
    print(
        "auditize version %s (using Python %s - %s)"
        % (__version__, platform.python_version(), sys.executable)
    )


async def async_main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", "-v", action="store_true", help="Print version information"
    )
    sub_parsers = parser.add_subparsers()

    # CMD migrate-db
    migrate_db_parser = sub_parsers.add_parser(
        "migrate-db", help="Create or update the Auditize database"
    )
    migrate_db_parser.set_defaults(func=lambda _: migrate_db())

    # CMD bootstrap-superadmin
    bootstrap_superadmin_parser = sub_parsers.add_parser(
        "bootstrap-superadmin", help="Create a superadmin user"
    )
    bootstrap_superadmin_parser.add_argument("email")
    bootstrap_superadmin_parser.add_argument("first_name")
    bootstrap_superadmin_parser.add_argument("last_name")
    bootstrap_superadmin_parser.set_defaults(
        func=lambda cmd_args: bootstrap_superadmin(
            cmd_args.email, cmd_args.first_name, cmd_args.last_name
        )
    )

    # CMD serve
    serve_parser = sub_parsers.add_parser("serve", help="Serve the application")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=8000, type=int)
    serve_parser.set_defaults(func=lambda cmd_args: serve(cmd_args.host, cmd_args.port))

    # CMD purge-expired-logs
    purge_expired_logs_parser = sub_parsers.add_parser(
        "purge-expired-logs", help="Purge expired logs"
    )
    purge_expired_logs_parser.add_argument(
        "repo",
        type=UUID,
        nargs="?",
        help="Optional repository ID to limit the purge to",
    )
    purge_expired_logs_parser.set_defaults(
        func=lambda cmd_args: purge_expired_logs(cmd_args.repo)
    )

    # CMD empty-repo
    empty_repo_parser = sub_parsers.add_parser(
        "empty-repo", help="Empty a log repository"
    )
    empty_repo_parser.add_argument("repo", type=UUID, help="Repository ID")
    empty_repo_parser.set_defaults(func=lambda cmd_args: empty_repo(cmd_args.repo))

    # CMD reindex
    reindex_repo_parser = sub_parsers.add_parser(
        "reindex",
        help="Reindex Elasticsearch index to the latest version",
    )
    reindex_repo_parser.add_argument(
        "repo",
        type=UUID,
        nargs="?",
        help="Optional repository ID to limit the reindex to",
    )
    reindex_repo_parser.set_defaults(func=lambda cmd_args: reindex_repo(cmd_args.repo))

    # CMD schedule
    schedule_parser = sub_parsers.add_parser(
        "schedule", help="Schedule Auditize periodic tasks"
    )
    schedule_parser.set_defaults(func=lambda _: schedule())

    # CMD config
    config_parser = sub_parsers.add_parser(
        "config", help="Dump the Auditize configuration as JSON"
    )
    config_parser.set_defaults(func=lambda _: dump_config())

    # CMD openapi
    openapi_parser = sub_parsers.add_parser("openapi", help="Dump the OpenAPI schema")
    openapi_parser.set_defaults(func=lambda _: dump_openapi())

    # CMD version
    version_parser = sub_parsers.add_parser("version", help="Print version information")
    version_parser.set_defaults(func=lambda _: version())

    parsed_args = parser.parse_args(args)

    if parsed_args.version:
        await version()
        return 0

    if not hasattr(parsed_args, "func"):
        parser.print_help()
        return 1

    await parsed_args.func(parsed_args)

    return 0


def main(args=None):
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
