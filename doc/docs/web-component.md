# Web Component

## How it works

Auditize let's you integrate the log interface right into your application frontend using a [Web Component](https://developer.mozilla.org/en-US/docs/Web/API/Web_components).

On your application frontend, you must first include the supporting JavaScript file into your HTML document:

```html
<script type="module" src="${BASE_URL}/auditize-web-component.mjs"></script>
```

Where `${BASE_URL}` is the URL of your Auditize instance.

Then, use the `<auditize-logs>` tag to include the log interface into your application:

```html
<auditize-logs
  base-url="${BASE_URL}"
  repo-id="${REPO_ID}"
  access-token-provider="getAccessToken"
/>
```

The tag supports the following attributes:

| Attribute | Required | Description |
| --- | --- | --- |
| `base-url` | **yes** | The URL of your Auditize instance. |
| `repo-id` | **yes** | The repository ID you want to display the logs from. |
| `access-token-provider` | **yes** | The name of a javascript function that retrieves an Auditize access token (and return it as a `Promise<string>`) from your own backend. |
| `access-token-refresh-interval` | no | The interval in milliseconds at which the access token is refreshed. Default is 300000 (5 minutes). |
| `lang` | no | The language to use in the Web Component (UI & log translatable content). Default is `en`. |

An access token is obtained by calling the [`/api/auth/access-token` endpoint](api.html#tag/auth/operation/generate_access_token) with an API key. This endpoint generates a short-lived access token (10 minutes by default) which can be used to delegate a sub-scope of permissions to a third-party application (such as the Web Component). The permissions can be any Auditize permission that the API key is allowed to use/grant. In the context of the Web Component, this typically involves granting read permission on the repository from which you want your users to view logs.

The request parameters passed to the `/api/auth/access-token` endpoint will look like this:

```json
{
  "permissions": {
    "logs": [
      {
        "repo_id": "${REPO_ID}",
        "read": true
      }
    ]
  }
}
```

Where `${REPO_ID}` is the same ID you passed to the `repo-id` attribute of the `<auditize-logs>` tag.

!!! warning
    As the access token is visible to your end-user, it should be scoped to the minimum required permissions, like in this example.

The call to the `/api/auth/access-token` Auditize endpoint must be done **from your backend** to keep the API key secret. The `access-token-provider` attribute of the `<auditize-logs>` tag is a JavaScript function that you must implement in your frontend to get the access token from your backend.

The [`AUDITIZE_ACCESS_TOKEN_LIFETIME` environment variable](config.md) defines the lifetime of the access token. Make sure that this value and the value of the `access-token-refresh-interval` attribute are consistent, meaning that the access token lifetime must be greater than the refresh interval.

## Example

Here is an example of a very basic web application, yet functionnal, written in Python using the [FastAPI](https://fastapi.tiangolo.com/) framework, which integrates the Auditize Web Component.

1. it serves an HTML page that includes the Auditize Web Component and a JavaScript function named `getAccessToken`
1. the web component calls the `getAccessToken` function
1. this function does a call to the `/access-token` endpoint of its own backend
1. this `/access-token` endpoint calls the Auditize `/api/auth/access-token` endpoint to get an actual access token and returns it to the frontend
1. the access token is made available to the Web Component and used to authenticate the user to Auditize
1. the `getAccessToken` function is then called every 5 minutes (the default refresh interval) to get a new access token

```python
import os

import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

AUDITIZE_URL = os.environ["AUDITIZE_URL"]
AUDITIZE_APIKEY = os.environ["AUDITIZE_APIKEY"]
AUDITIZE_REPO = os.environ["AUDITIZE_REPO"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <script type="module" src="{base_url}/auditize-web-component.mjs"></script>
        <script>
            function getAccessToken() {{
                return fetch("/access-token")
                    .then(response => response.json())
                    .then(data => data.access_token);
            }}
        </script>
    </head>
    <body>
        <h1 style="text-align: center">Auditize Web Component Demo</h1>
        <auditize-logs
          base-url="{base_url}"
          repo-id="{repo_id}"
          access-token-provider="getAccessToken"
        />
    </body>
</html>
"""


def get_access_token():
    resp = requests.post(
        f"{AUDITIZE_URL}/api/auth/access-token",
        json={
            "permissions": {
                "logs": {"repos": [{"repo_id": AUDITIZE_REPO, "read": True}]}
            }
        },
        headers={
            "Authorization": f"Bearer {AUDITIZE_APIKEY}",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


app = FastAPI()


@app.get("/access-token")
def access_token():
    return {"access_token": get_access_token()}


@app.get("/")
def index():
    return HTMLResponse(
        content=HTML_TEMPLATE.format(
            base_url=AUDITIZE_URL,
            repo_id=AUDITIZE_REPO,
        )
    )
```

To ensure your browser can properly interpret responses from the Auditize API, you must enable CORS requests for your Auditize instance. Please refer to the CORS options in the [Configuration](config.md) section.

The Github repository containing this example is available [here](https://github.com/auditize/auditize-webcomponent-demo).

## Limitations

The Auditize Web Component is designed to offer a simplified view of a specific log scope, rather than providing all the features of the standard log interface. As a result, it has some limitations.

As previously mentioned, the repository selection is controlled by the `repo-id` attribute of the `<auditize-logs>` tag. Therefore, unlike the standard log interface, the Web Component can **only display logs from a single repository**.

Additionally, **Log filters are not available** in the Web Component.