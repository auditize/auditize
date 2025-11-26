#!/usr/bin/env python

import json
import os
import sys

import httpx


def format_number(number: int, total: int) -> str:
    return str(number % total).zfill(len(str(total)))


def create_value(prefix: str, counter: int, total: int) -> str:
    return "%s-%s" % (prefix, format_number(counter, total))


def create_log(counter: int):
    log = {
        "action": {
            "category": create_value("action-category", counter, 10),
            "type": create_value("action-type", counter, 100),
        },
        "actor": {
            "ref": create_value("user", counter, 1000),
            "type": "user",
            "name": create_value("user", counter, 1000),
            "extra": [
                {
                    "name": create_value("plain-value-name", counter, 3),
                    "value": create_value("plain value", counter, 10),
                },
                {
                    "name": create_value("enum-value-name", counter, 3),
                    "value": create_value("enum_value", counter, 3),
                    "type": "enum",
                },
                {
                    "name": create_value("boolean-value-name", counter, 3),
                    "value": True if counter % 2 == 0 else False,
                    "type": "boolean",
                },
            ],
        },
        "source": [
            {
                "name": create_value("plain-value-name", counter, 5),
                "value": create_value("plain value", counter, 50),
            },
            {
                "name": create_value("enum-value-name", counter, 5),
                "value": create_value("enum_value", counter, 3),
                "type": "enum",
            },
            {
                "name": create_value("boolean-value-name", counter, 5),
                "value": True if counter % 2 == 0 else False,
                "type": "boolean",
            },
        ],
        "resource": {
            "ref": create_value("resource", counter, 1000),
            "type": create_value("resource", counter, 50),
            "name": create_value("resource", counter, 1000),
            "extra": [
                {
                    "name": create_value("plain-value-name", counter, 3),
                    "value": create_value("plain value", counter, 10),
                },
                {
                    "name": create_value("enum-value-name", counter, 3),
                    "value": create_value("enum_value", counter, 3),
                    "type": "enum",
                },
                {
                    "name": create_value("boolean-value-name", counter, 5),
                    "value": True if counter % 2 == 0 else False,
                    "type": "boolean",
                },
            ],
        },
        "details": [
            {
                "name": create_value("plain-value-name", counter, 10),
                "value": create_value("plain value", counter, 100),
            },
            {
                "name": create_value("enum-value-name", counter, 10),
                "value": create_value("enum_value", counter, 3),
                "type": "enum",
            },
            {
                "name": create_value("boolean-value-name", counter, 10),
                "value": True if counter % 2 == 0 else False,
                "type": "boolean",
            },
        ],
        "tags": [
            {
                "type": create_value("simple-tag-type", counter, 3),
            },
            {
                "ref": create_value("rich-tag", counter, 1000),
                "type": create_value("rich-tag-type", counter, 3),
                "name": create_value("rich-tag-name", counter, 1000),
            },
        ],
        "entity_path": [
            {
                "ref": create_value("customer", counter, 10),
                "name": create_value("Customer", counter, 10),
            },
            {
                "ref": create_value(
                    "customer_%s_entity" % format_number(counter, 10), counter, 100
                ),
                "name": create_value("Entity", counter, 100),
            },
        ],
    }
    attachments = [
        {
            "name": "file.txt",
            "data": b"Hello, World!",
            "type": "text",
        }
    ]
    return log, attachments


def jsonify(data):
    return json.dumps(data, indent=4, ensure_ascii=False)


def inject_log(base_url, repo_id, api_key, log, attachments):
    resp = httpx.post(
        f"{base_url}/api/repos/{repo_id}/logs",
        headers={"Authorization": f"Bearer " + api_key},
        json=log,
    )
    if not resp.is_success:
        sys.exit(
            "Error %s while pushing log:\n%s" % (resp.status_code, jsonify(resp.json()))
        )
    log_id = resp.json()["id"]
    for attachment in attachments:
        resp = httpx.post(
            f"{base_url}/api/repos/{repo_id}/logs/{log_id}/attachments",
            headers={"Authorization": f"Bearer " + api_key},
            files={"file": (attachment["name"], attachment["data"])},
            data={
                "type": attachment["type"],
            },
        )
        if not resp.is_success:
            sys.exit(
                "Error %s while pushing attachment: %s"
                % (resp.status_code, jsonify(resp.json()))
            )


def main(argv):
    if len(argv) != 2:
        sys.exit("Usage: %s COUNT" % argv[0])

    try:
        base_url = os.environ["AUDITIZE_URL"]
        repo_id = os.environ["AUDITIZE_REPO"]
        api_key = os.environ["AUDITIZE_APIKEY"]
    except KeyError as e:
        sys.exit("Missing environment variable: %s" % e)

    count = int(argv[1])

    for i in range(count):
        print("Inject log %d of %d" % (i + 1, count), end="\r")
        log, attachments = create_log(i + 1)
        inject_log(base_url, repo_id, api_key, log, attachments)
    print()


if __name__ == "__main__":
    main(sys.argv)
