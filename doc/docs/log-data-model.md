# Log data model

## Overview

Here is an example of a full-featured log such as it is accepted by the `POST /api/repos/{id}/logs` API endpoint:

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
  "entity_path": [
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
- what the action is about (`resource`),
- the details of the action (`details`),
- the entity to which the log is related (`entity_path`).

The structure is also flexible enough to let you add custom information about the actor, the source, the resource, the details and through the tag system.

## Anatomy of a log

!!! info
    Values that must respect the `[a-z0-9-]+` format are used as translation keys that 
    can be translated through [Log i18n Profiles](overview.md#log-i18n-profiles).
    When no translation is available for a given key, a default translation is inferred
    from the key itself by the UI.


### `action`

The `action` object specifies the action being performed. It includes the following fields:

- `type`: It should describe the action in a non-ambiguous way, independent of its associated `category`. For example, if you want to describe the creation of a user, `user-creation` is preferable to `create`. This field is required and must respect the `[a-z0-9-]+` format.
- `category`: It is used to group related types of actions. For example, you could use `user-management` for actions whose `type` is `user-creation`, `user-deletion`, etc. This field is required and must respect the `[a-z0-9-]+` format.

The `action` object is mandatory.

### `source`

The `source` object holds information about the source of the action. It is normalized as a list of custom fields and can be used to express any information: the application that triggered the action, the version of the application, an IP address, etc.

A custom field must include the following fields:

- `name`: The source field name. It must respect the `[a-z0-9-]+` format.
- `value`: The source field value. It can be any string.

The `source` field is optional.

### `actor`

The `actor` object identifies the actor behind the action. It includes the following fields:

- `ref`: A value that uniquely identifies an actor, regardless of its `type`. This field is required and can be any string.
- `type`: The type of the actor. This field is required and must respect the `[a-z0-9-]+` format.
- `name`: The name of the actor. This field is required and can be any string.
- `extra`: An optional list of custom fields that can be used to express any extra custom information about the actor such as an email, a role, etc.

The `actor` object is optional.


### `resource`

The `resource` object identifies the resource being the target of the action. It includes the following fields:

- `ref`: A value that uniquely identifies a resource, regardless of its `type`. This field is required and can be any string.
- `type`: The type of the resource. This field is required and must respect the `[a-z0-9-]+` format.
- `name`: The name of the resource. This field is required and can be any string.
- `extra`: A list of custom fields that can be used to express any extra custom information about the resource. The `name` must respect the `[a-z0-9-]+` format while the `value` can be any string.

The `resource` object is optional.


### `details`

The `details` object holds information about the action. It follows the same structure as the `source` object but is used to proovide details about the action itself.


### `tags`

`tags` is a list of elements that can be used to track logs on an arbitrary basis. There are two types of tags:

- "simple" tags: they are represented by an object with only a `type` field. The `type` must respect the `[a-z0-9-]+` format.
- "rich" tags: they are represented by an object with the three required fields: 
    - `type` (must respect the `[a-z0-9-]+` format),
    - `ref` (a value that uniquely identifies a resource, whatever its type)
    - and `name` (can be any string)

### `entity_path`

Auditize represents the entities of your application as a hierarchical tree structure. Entities can be anything: a customer company, an organizational unit, a geographical location, etc. Each log must include the full path to the specific entity it is associated with. Example: if your application's organization is divided into regions, states, and cities, and a log is about a job offer in Arlington, Texas, its `entity_path` could be:

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

`entity_path` is required and must include at least one element, the `ref` and `name` fields are mandatory for each element of the list.

By including the full path to each entity, Auditize can construct a tree structure of your entities and display it within the log interface. This allows you to filter logs by entity and navigate through the tree to view logs associated with a specific entity. Although this feature may not be relevant to the previous example, Auditize is also capable of updating its internal tree structure when logs expire or when entities are renamed or moved. The original log path remains unchanged.

## Attachments

Auditize supports file attachements to logs. To upload one or more files to a log, you must first create the log and then attach the file(s) using the `POST /api/repos/{repo_id}/logs/{log_id}/attachments` endpoint. In addition to the file content itself, you can specify the following:

- `type`: The type of the attachment. This field is required and must follow the `[a-z0-9-]+` format.
- `name`: The name of the attachment. f not provided, it defaults to the uploaded file's name.
- `mime_type`: The MIME type of the attachment. If not provided, it defaults to the MIME type of the uploaded file.
