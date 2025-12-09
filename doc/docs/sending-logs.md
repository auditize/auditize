# Sending logs

After Auditize is successfully installed, two steps are still necessary to send logs:

- Create a [log repository](overview.md#log-repositories).
- Create an [API key](overview.md#api-keys) with at least write permission for this repository and obtain the associated secret (referred to as the API key throughout the rest of this page).

Here is an example of sending a log to Auditize using `curl`:

```bash
curl \
  ${AUDITIZE_URL}/api/repos/${AUDITIZE_REPO}/logs \
  -H "Authorization: Bearer ${AUDITIZE_APIKEY}" \
  --json '{"action": {"type": "user_login", "category": "authentication"}, "actor": {"name": "John Doe", "ref": "john.doe@example.net", "type": "user"}, "entity_path": [{"ref": "1", "name": "Customer A"}]}'
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
        "action": {"type": "user_login", "category": "authentication"},
        "actor": {"name": "John Doe", "ref": "john.doe@example.net", "type": "user"},
        "entity_path": [{"ref": "1", "name": "Customer A"}],
    },
)
resp.raise_for_status()
print(resp.text)
```

!!! info "See also"
    - [Log data model](log-data-model.md)
    - [POST /api/repos/{repo_id}/logs API documentation](api.html#tag/log/operation/create_log)
    - [POST /api/repos/{repo_id}/logs/{log_id}/attachments API documentation](api.html#tag/log/operation/add_log_attachment)
