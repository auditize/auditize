# Log data model

## Overview

Here is an example of log such as it is accepted by `POST /api/repos/{id}/logs`:

```json
{
  "action": {
    "type": "job-offer-creation",
    "category": "job-offers"
  },
  "source": [
    {
      "name": "application",
      "value": "myATS"
    },
    {
      "name": "application-version",
      "value": "1.0.0"
    }
  ],
  "actor": {
    "ref": "418b0dc2-5fbc-4e5b-bab2-ba03250455e5",
    "type": "user",
    "name": "John Pierce",
    "extra": [
      {
        "name": "email",
        "value": "john.pierce@example.com"
      }
    ]
  },
  "resource": {
    "ref": "d37cf866-a4f8-4146-8c04-f6045b8c7502",
    "type": "job-offer",
    "name": "Social Media Manager in Arlington",
    "extra": []
  },
  "details": [
    {
      "name": "job-title",
      "value": "Social Media Manager"
    }
  ],
  "tags": [
    {
      "type": "important"
    }
  ],
  "node_path": [
    {
      "ref": "860cb19d-4660-4ec6-b596-c9dcefc293e5",
      "name": "South"
    },
    {
      "ref": "a4cdd5d5-f41a-44cd-838c-dd99b29b8d55",
      "name": "Texas"
    },
    {
      "ref": "a6a34c64-12c9-44ac-8a06-f4b99c3205d0",
      "name": "Arlington"
    }
  ],
}
```

This structure let's you represent :

- the action being performed (`action`),
- who is performing the action (`actor`),
- the target of the action (`resource`),
- the details of the action (`details`),
- the entity to which the log is related (`node_path`).

The structure is also flexible enough to let you add any custom information about the actor, the source, the resource, the details and through a tag system.

## Details

!!! info
    Values that must respect the `[a-z0-9-]+` can be translated through [Log i18n Profiles](overview#log-i18n-profiles), they are also used to form a human-friendly name in the log interface when no translation is available.


### `action`

The `action` object describes the action that was performed. It contains the following fields:

- `type`: The type of the action. It should describe the action in a non-ambiguous way. For instance, if you want to describe the creation of a user, you could use `user-creation` over `create`. It must respect the `[a-z0-9-]+` format.
- `category`: The category of the action is used to group actions of the same nature. For instance, you could use `user-management` for actions whose `type` is `user-creation`, `user-deletion`, etc. It must respect the `[a-z0-9-]+` format.

The `action` object is mandatory as its `type` and `category` fields.


### `source`

The `source` object holds information about the source of the action. It is normalized as a list of name-value objects (also named "custom fields") and can be used to express any information: the application that triggered the action, the version of the application, a IP address, etc.

- `name`: The name of the source field. It must respect the `[a-z0-9-]+` format.
- `value`: The value of the source field. It can be any string.

The `source` field list is optional but for a given field object, both `name` and `value` are mandatory.


### `actor`

The `actor` object describes the actor that performed the action. It contains the following fields:

- `ref`: The unique identifier of the actor, it must be unique across all actors, whatever their type. It can be a UUID or any other unique identifier as long as it is expressed as a string.
- `type`: The type of the actor. It must respect the `[a-z0-9-]+` format.
- `name`: The name of the actor. It can be any string.
- `extra`: A list of custom fields that can be used to express any extra custom information about the actor such as an email, a role, etc. The `name` must respect the `[a-z0-9-]+` format while the `value` can be any string.

The `actor` object is optional but if it is present, the `ref`, `type`, and `name` fields are mandatory.


### `resource`

The `resource` object describes the resource that was the target of the action. It contains the following fields:

- `ref`: A value that uniquely identifies a resource, whatever its type. It can be a UUID or any other unique identifier as long as it is expressed as a string.
- `type`: The type of the resource. It must respect the `[a-z0-9-]+` format.
- `name`: The name of the resource. It can be any string.
- `extra`: A list of custom fields that can be used to express any extra custom information about the resource. The `name` must respect the `[a-z0-9-]+` format while the `value` can be any string.

The `resource` object is optional but if it is present, the `ref`, `type`, and `name` fields are mandatory.


### `details`

The `details` object holds information about the action. It follows the same structure as the `source` object but is used to express details about the action itself.


### `tags`

`tags` is a list of elements that can be used to follow / group logs on an arbitrary basis. There are two types of tags:

- "simple" tags: they are represented by an object with only a `type` field. The `type` must respect the `[a-z0-9-]+` format.
- "rich" tags: they are represented by an object with the three required fields: 
    - `type` (must respect the `[a-z0-9-]+` format),
    - `ref` (a value that uniquely identifies a resource, whatever its type)
    - and `name` (can be any string)

### `node_path`

Auditize supports a hierarchical tree structure to represent the entities of your application. Entities can be anything: a customer, an organizational unit, a geographical location, etc. Each log must contain the full path to the entity that is the subject of the log. Example: if the log is about a job offer in Arlington, Texas, the `node_path` would be:

```json
[
  {
    "ref": "860cb19d-4660-4ec6-b596-c9dcefc293e5",
    "name": "South"
  },
  {
    "ref": "a4cdd5d5-f41a-44cd-838c-dd99b29b8d55",
    "name": "Texas"
  },
  {
    "ref": "a6a34c64-12c9-44ac-8a06-f4b99c3205d0",
    "name": "Arlington"
  }
]
```

Where:

- `ref` is the unique identifier of the entity
- `name` is the name of the entity

`node_path` is required and must contain at least one element, the `ref` and `name` fields are mandatory for each element of the list.

With each log containing the full path to the entity, Auditize is able to build a tree structure of your entities and display it in the log interface. This will allow you to filter logs by entity and navigate through the tree to see logs related to a specific entity. While it is not relevant in this example, Auditize is also able to update its internal tree structure at log expiration and when entities are renamed or moved. The original path of the log is left untouched.

## Attachments

Auditize supports file attachements to logs. When you want to upload one or more files to a log, you must first create the log and then attach the file to the log through the `POST /api/repos/{repo_id}/logs/{log_id}/attachments` endpoint. Beside the file content itself, you can provide:

- `type`: The type of the attachment. It must respect the `[a-z0-9-]+` format, this field is required
- `name`: The name of the attachment. It defaults to the uploaded file name if not provided
- `mime_type`: The MIME type of the attachment. It defaults to the MIME type of the uploaded file if not provided
