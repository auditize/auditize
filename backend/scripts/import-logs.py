#!/usr/bin/env python

import asyncio
import json
import os
import sys
from typing import Iterator

import httpx


async def import_log(client, base_url, repo_id, api_key, log_data):
    resp = await client.post(
        f"{base_url}/api/repos/{repo_id}/logs/import",
        headers={"Authorization": f"Bearer {api_key}"},
        json=log_data,
    )
    if resp.is_error:
        print(resp.text, file=sys.stderr)
    resp.raise_for_status()


def read_logs() -> Iterator[dict]:
    for line in sys.stdin:
        if not line.strip():
            continue
        yield json.loads(line)


# Adapted from https://death.andgravity.com/limit-concurrency#asyncio-wait
async def run_concurrently(aws: Iterator, limit: int):
    aws_ended = False
    pending = set()

    while pending or not aws_ended:
        while len(pending) < limit and not aws_ended:
            try:
                aw = next(aws)
            except StopIteration:
                aws_ended = True
            else:
                pending.add(asyncio.create_task(aw))

        if not pending:
            return

        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        while done:
            yield done.pop()


async def import_logs(base_url, repo_id, api_key):
    log_idx = 0
    async with httpx.AsyncClient() as client:
        log_imports = (
            import_log(client, base_url, repo_id, api_key, log_data)
            for log_data in read_logs()
        )
        async for task in run_concurrently(log_imports, limit=20):
            await task
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

    asyncio.run(import_logs(base_url, repo_id, api_key))


if __name__ == "__main__":
    main(sys.argv)
