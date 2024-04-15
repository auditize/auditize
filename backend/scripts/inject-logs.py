#!/usr/bin/env python

import sys
import json

import requests


def format_number(number: int, total: int) -> str:
    return str(number % total).zfill(len(str(total)))


def create_value(prefix: str, counter: int, total: int) -> str:
    return "%s_%s" % (
        prefix, format_number(counter, total)
    )


def create_log(counter: int):
    return {
        "event": {
            "category": create_value("event_category", counter, 10),
            "name": create_value("event_name", counter, 100),
        },
        "actor": {
            "type": "user",
            "id": create_value("user", counter, 1000),
            "name": create_value("user", counter, 1000),
        },
        "resource": {
            "type": create_value("resource", counter, 50),
            "id": create_value("resource", counter, 1000),
            "name": create_value("resource", counter, 1000),
        },
        "context": {
            create_value("more_details", counter, 5): {
                create_value("some_key", counter, 10): create_value("some_value", counter, 10),
            },
        },
        "trackings": [
            {
                "type": create_value("tracking", counter, 3),
                "id": create_value("tracking_id", counter, 1000),
                "name": create_value("tracking_id", counter, 1000),
            }
        ],
        "node_path": [
            {
                "id": create_value("customer", counter, 10),
                "name": create_value("Customer", counter, 10),
            },
            {
                "id": create_value(
                    "customer_%s_entity" % format_number(counter, 10), counter, 100
                ),
                "name": create_value("Entity", counter, 100),
            }
        ]
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: %s REPO_ID" % sys.argv[0])

    base_url = "http://localhost:8000"
    repo_id = sys.argv[1]
    count = 10_000

    for i in range(count):
        print("Inject log %d of %d" % (i+1, count), end="\r")
        log = create_log(i)
        resp = requests.post(f"{base_url}/repos/{repo_id}/logs", json=log)
        if not resp.ok:
            print()
            print("Error: %s" % json.dumps(resp.json(), indent=4, ensure_ascii=False))
            break
    print()
