#!/usr/bin/env python

import glob
import json
import os
import sys
from itertools import count

import httpx


def import_logs(base_url, repo_id, api_key, source_dir):
    for log_idx, filename in enumerate(glob.glob(f"{source_dir}/*.json")):
        with open(filename, "r") as fh:
            log_data = json.load(fh)
        resp = httpx.post(
            f"{base_url}/api/repos/{repo_id}/logs/import",
            headers={"Authorization": f"Bearer {api_key}"},
            json=log_data,
        )
        resp.raise_for_status()
        print(f"Imported {log_idx+1:08d}", end="\r")


def main(argv):
    try:
        source_dir = argv[1]
    except IndexError:
        sys.exit("Usage: %s SOURCE_DIRECTORY" % argv[0])

    try:
        base_url = os.environ["AUDITIZE_URL"]
        repo_id = os.environ["AUDITIZE_REPO"]
        api_key = os.environ["AUDITIZE_APIKEY"]
    except KeyError as e:
        sys.exit("Missing environment variable: %s" % e)

    import_logs(base_url, repo_id, api_key, source_dir)


if __name__ == "__main__":
    main(sys.argv)
