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


def download_logs(base_url, repo_id, api_key, target_dir):
    for log_idx, log in enumerate(get_logs(base_url, repo_id, api_key)):
        filename = f"{target_dir}/{log_idx+1:08d}.json"
        with open(filename, "w") as fh:
            json.dump(log, fh, ensure_ascii=False)
        print(f"Wrote {filename}", end="\r")


def main(argv):
    try:
        target_dir = argv[1]
    except IndexError:
        sys.exit("Usage: %s TARGET_DIRECTORY" % argv[0])

    try:
        base_url = os.environ["AUDITIZE_URL"]
        repo_id = os.environ["AUDITIZE_REPO"]
        api_key = os.environ["AUDITIZE_APIKEY"]
    except KeyError as e:
        sys.exit("Missing environment variable: %s" % e)

    os.makedirs(target_dir, exist_ok=True)

    download_logs(base_url, repo_id, api_key, target_dir)


if __name__ == "__main__":
    main(sys.argv)
