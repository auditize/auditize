# Sending logs

Once Auditize has been properly installed, you must:

- create a [log repository](overview.md#log-repositories)
- create an [API key](overview.md#api-keys) with (at least) the write permission on this repository and get the secret associated with this key (that's what we'll name API key in the rest of this page)

Here is an example of sending a log to Auditize using `curl`:

```bash
curl \
  ${AUDITIZE_URL}/api/repos/${AUDITIZE_REPO}/logs \
  -H "Authorization: Bearer ${AUDITIZE_APIKEY}" \
  --json '{"action": {"type": "user-login", "category": "authentication"}, "actor": {"name": "John Doe", "ref": "john.doe@example.net", "type": "user"}, "node_path": [{"ref": "1", "name": "Customer A"}]}'
```

Here is the same example using Python and [requests](https://docs.python-requests.org/en/master/):

```python
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
```