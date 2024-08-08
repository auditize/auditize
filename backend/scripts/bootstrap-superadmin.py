#!/usr/bin/env python

import asyncio
import getpass
import sys

from auditize.database import get_dbm
from auditize.exceptions import UnknownModelException
from auditize.permissions.models import Permissions
from auditize.user.models import User
from auditize.user.service import get_user_by_email, hash_user_password, save_user


def get_password() -> str:
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match, please try again.", file=sys.stderr)
        print("", file=sys.stderr)
        return get_password()

    return password


async def main():
    if len(sys.argv) != 4:
        sys.exit(f"Usage: {sys.argv[0]} EMAIL FIRST_NAME LAST_NAME")

    dbm = get_dbm()

    email, first_name, last_name = sys.argv[1:]
    password = get_password()

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


if __name__ == "__main__":
    asyncio.run(main())
