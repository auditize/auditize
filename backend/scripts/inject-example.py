#!/usr/bin/env python3

import os

import requests

resp = requests.post(
    f"{os.environ['AUDITIZE_URL']}/api/repos/{os.environ['AUDITIZE_REPO']}/logs",
    headers={"Authorization": f"Bearer {os.environ['AUDITIZE_APIKEY']}"},
    json={
        "action": {"type": "user-login", "category": "authentication"},
        "actor": {"name": "John Doe", "ref": "john.doe@example.net", "type": "user"},
        "node_path": [{"ref": "1", "name": "Customer A"}],
    },
)
resp.raise_for_status()
print(resp.text)
