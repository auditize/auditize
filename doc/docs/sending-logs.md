# Sending logs

Once Auditize has been properly installed, two steps are required to send logs:

- creating a [log repository](overview.md#log-repositories)
- creating an [API key](overview.md#api-keys) with (at least) the write permission on this repository and getting the secret associated to this key (that's what we'll name API key in the rest of this page)

An example of sending a log to Auditize using `curl`:

```bash
curl \
  ${AUDITIZE_URL}/api/repos/${AUDITIZE_REPO}/logs \
  -H "Authorization: Bearer ${AUDITIZE_APIKEY}" \
  --json '{"action": {"type": "user-login", "category": "authentication"}, "actor": {"name": "John Doe", "ref": "john.doe@example.net", "type": "user"}, "node_path": [{"ref": "1", "name": "Customer A"}]}'
```

Another example using Python and [requests](https://docs.python-requests.org/en/master/):

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

!!! info "See also"
    - [the endpoint detailed documentation](api.html#tag/log/operation/create_log)
    - [how to attach a file to a log](api.html#tag/log/operation/add_log_attachment)
