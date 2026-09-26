#!/usr/bin/env python

import json
import os
import sys
from typing import Iterator

import httpx


def get_logs(base_url: str, repo_id: str, api_key: str) -> Iterator[dict]:
    cursor = None
    while True:
        resp = httpx.get(
            f"{base_url}/api/repos/{repo_id}/logs",
            params={"cursor": cursor} if cursor else {},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        yield from data["items"]
        cursor = data["pagination"]["next_cursor"]
        if not cursor:
            break


def download_logs(base_url, repo_id, api_key):
    log_idx = None
    for log_idx, log in enumerate(get_logs(base_url, repo_id, api_key)):
        sys.stdout.write(json.dumps(log, ensure_ascii=False) + "\n")
        print(f"Downloaded {log_idx + 1}", end="\r", file=sys.stderr)

    if log_idx is not None:
        print(file=sys.stderr)


def main(argv):
    if len(argv) != 1:
        sys.exit("Usage: %s > LOGS.jsonl" % argv[0])

    try:
        base_url = os.environ["AUDITIZE_URL"]
        repo_id = os.environ["AUDITIZE_REPO"]
        api_key = os.environ["AUDITIZE_APIKEY"]
    except KeyError as e:
        sys.exit("Missing environment variable: %s" % e)

    download_logs(base_url, repo_id, api_key)


if __name__ == "__main__":
    main(sys.argv)
