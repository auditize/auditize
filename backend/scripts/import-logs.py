#!/usr/bin/env python

import json
import os
import sys

import httpx


def import_logs(base_url, repo_id, api_key):
    log_idx = 0
    for line in sys.stdin:
        if not line.strip():
            continue
        log_data = json.loads(line)
        resp = httpx.post(
            f"{base_url}/api/repos/{repo_id}/logs/import",
            headers={"Authorization": f"Bearer {api_key}"},
            json=log_data,
        )
        resp.raise_for_status()
        log_idx += 1
        print(f"Imported {log_idx}", end="\r", file=sys.stderr)

    if log_idx:
        print(file=sys.stderr)


def main(argv):
    if len(argv) != 1:
        sys.exit("Usage: %s < LOGS.jsonl" % argv[0])

    try:
        base_url = os.environ["AUDITIZE_URL"]
        repo_id = os.environ["AUDITIZE_REPO"]
        api_key = os.environ["AUDITIZE_APIKEY"]
    except KeyError as e:
        sys.exit("Missing environment variable: %s" % e)

    import_logs(base_url, repo_id, api_key)


if __name__ == "__main__":
    main(sys.argv)
