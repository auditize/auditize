#!/usr/bin/env python

import json
import sys

import requests


def format_number(number: int, total: int) -> str:
    return str(number % total).zfill(len(str(total)))


def create_value(prefix: str, counter: int, total: int) -> str:
    return "%s_%s" % (prefix, format_number(counter, total))


def create_log(counter: int):
    log = {
        "action": {
            "category": create_value("action_category", counter, 10),
            "type": create_value("action_type", counter, 100),
        },
        "actor": {
            "ref": create_value("user", counter, 1000),
            "type": "user",
            "name": create_value("user", counter, 1000),
            "extra": [
                {
                    "name": create_value("actor_extra_name", counter, 3),
                    "value": create_value("actor_extra_value", counter, 10),
                }
            ],
        },
        "source": [
            {
                "name": create_value("source_name", counter, 5),
                "value": create_value("source_value", counter, 50),
            }
        ],
        "resource": {
            "ref": create_value("resource", counter, 1000),
            "type": create_value("resource", counter, 50),
            "name": create_value("resource", counter, 1000),
            "extra": [
                {
                    "name": create_value("resource_extra_name", counter, 3),
                    "value": create_value("resource_extra_value", counter, 10),
                }
            ],
        },
        "details": [
            {
                "name": create_value("detail_name", counter, 10),
                "value": create_value("detail_value", counter, 100),
            }
        ],
        "tags": [
            {
                "type": create_value("simple_tag_type", counter, 3),
            },
            {
                "ref": create_value("rich_tag", counter, 1000),
                "type": create_value("rich_tag_type", counter, 3),
                "name": create_value("rich_tag_name", counter, 1000),
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
    resp = requests.post(
        f"{base_url}/repos/{repo_id}/logs",
        headers={"Authorization": f"Bearer " + api_key},
        json=log,
    )
    if not resp.ok:
        sys.exit(
            "Error %s while pushing log:\n%s" % (resp.status_code, jsonify(resp.json()))
        )
    log_id = resp.json()["id"]
    for attachment in attachments:
        resp = requests.post(
            f"{base_url}/repos/{repo_id}/logs/{log_id}/attachments",
            headers={"Authorization": f"Bearer " + api_key},
            files={"file": (attachment["name"], attachment["data"])},
            data={
                "type": attachment["type"],
            },
        )
        if not resp.ok:
            sys.exit(
                "Error %s while pushing attachment: %s"
                % (resp.status_code, jsonify(resp.json()))
            )


def main(argv):
    if len(argv) != 4:
        sys.exit("Usage: %s COUNT REPO_ID API_KEY" % argv[0])

    base_url = "http://localhost:8000"
    count = int(argv[1])
    repo_id = argv[2]
    api_key = argv[3]

    for i in range(count):
        print("Inject log %d of %d" % (i + 1, count), end="\r")
        log, attachments = create_log(i)
        inject_log(base_url, repo_id, api_key, log, attachments)
    print()


if __name__ == "__main__":
    main(sys.argv)
    if len(sys.argv) != 4:
        sys.exit("Usage: %s COUNT REPO_ID API_KEY" % sys.argv[0])
