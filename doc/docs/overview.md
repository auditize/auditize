# Overview

Auditize aims to deliver powerful audit log management capabilities to your software without the burden of developing an in-house solution.

It is written in Python, it provides a REST API written in [FastAPI](https://fastapi.tiangolo.com) and a web interface written in [React](https://react.dev). It uses [PostgresQL](https://www.postgresql.org/) as a database and [Elasticsearch](https://www.elastic.co/elasticsearch) for log storage and search.

Here are the core concepts of Auditize:

## Log Repositories

Log Repositories (also referred to as "Repositories" or "Repos") serve as containers for logs. Each Log Repository is associated with a **dedicated Elasticsearch index**, ensuring strong isolation between logs. They allow you to set up specific permissions and settings, such as a retention periods or statuses.

You can set up one or more repositories based on your needs. However, to ensure logs consistency you should make sure that a given log repository only contains logs from the same application running in the same environment. You should for instance avoid mixing logs from a pre-production and production environment or logs from different unrelated applications in the same repository.

The following settings can be configured for a repository:

- Retention period: the time after which logs are automatically deleted
- Status:
    - Enabled: logs can be written and read
    - Read-only: logs can only be read
    - Disabled: logs cannot be read nor written
- [Log i18n Profile](#log-i18n-profiles): the profile used to translate logs in the web interface


## Users

Users are meant to access Auditize through the web interface. See [API keys](#api-keys) if you want to access the REST API programmatically.
When a user is created, they will receive an email with a link to set their password (make sure that [SMTP settings](config.md) are properly set). Once the password it set, the user will be able to log in to the web interface. Please refer to the [Permissions](#permissions) section for permissions details.

!!! note
    You'll notice that certain permissions or combination of permissions do not seem to make sense for a user. For instance:
    
    - a user with the "write" permission on the logs of a repository (while it's not possible to send logs through the web interface)
    - a user with only the "write" permission on resource management without the corresponding "read" permission

    This is because the permissions are used for API keys and are also employed to determine what permissions a [user can grant to other users](#granting-permissions).


## API keys

API keys are used to access Auditize programmatically through the REST API. Like [Users](#users), API keys have a set of [Permissions](#permissions). When a new API key is created, a secret is generated and only shown once. A new secret can be generated for an existing API key (if you lose the secret for instance). In this case, the former secret will no longer be valid.


## Permissions

!!! info
    In this section, we'll refer to "users" but the same applies to API keys.

Permissions are used to provide access to certain features of Auditize. Permissions can be set on [Users](#users) and [API keys](#api-keys). There are two categories of permissions:

- Management permissions
- Log permissions


### Management permissions

Management permissions allow you to administrate the various core resources of Auditize:

- Repositories (it also covers Log i18n Profiles)
- Users
- API keys

On each of these resources, you can set the following permissions:

- Read: it allows the user to view the resource
- Write: it allows the user to alter or delete the resource

!!! info
    Setting a read permission to a user without the write permission is like giving an audit access to the resource.


### Log permissions

Log permissions control the access to logs. Permissions can be set either globally or on an per repository basis.

- the "Read" permission allows the user to view logs
- the "Write" permission allows the user to send logs to the Auditize API

You can also also restrict the read permission to certain log entities instead of the whole repository by setting the "Entities" field rather than the "Read" field.


### Superadmin role

When a user is granted the Superadmin role, he has all permissions on all resources and logs.

!!! warning
    The Superadmin role should be granted with caution and be limited to a small number of users. Setting fine grained permissions to users is recommended.


### Granting permissions

When a user has the permission to manage Users or API keys ("write" permission), the permissions he is allowed to grant are the ones he has himself. For example, if a user has the "read" permission on a given repository logs, he is only able to grant the "read" permission on this repository to other users.

Please note that you need a "read" permission on a repository's logs without entity restrictions to grant the "read" permission (with or without entity restrictions) to this repository's logs to other users.


### Permissions normalization

When saving permissions, they are normalized to ensure consistency and avoid possible side effects in future permissions updates. The normalization process is as follows:

- if a user has a global "read" log permission (on all repositories), any "read" permission explicitly granted on a specific repository (with/without log entity restrictions) is removed
- if a user has a global "write" log permission (on all repositories), any "write" permission explicitly granted on a specific repository is removed
- if a user has the superadmin role, every explicitly granted management/logs permission is removed


## Log i18n Profiles

Auditize supports the internationalization of both the web interface and the logs themselves. Log internationalization is managed through Log i18n Profiles. Log i18n Profiles let you upload translation files for the languages you want to support (and are supported by Auditize).
The log translation applies to log fields whose value is considered to be a key. Here are the log field type that can be translated:

- `action_type`
- `action_category`
- `actor_type`
- `actor_custom_field` (extra field names of the actor)
- `actor_custom_field_enum_value` (extra field enum values of the actor)
- `source_field` (field names within the source)
- `source_custom_field_enum_value` (extra field enum values of the source)
- `detail_field` (field names within the details)
- `detail_custom_field_enum_value` (extra field enum values of the details)
- `resource_type`
- `resource_custom_field` (extra field names of the resource)
- `resource_custom_field_enum_value` (extra field enum values of the resource)
- `tag_type`
- `attachment_type`

Example of a translation file:

```json
{
  "action_type": {
    "job_offer_creation": "New job offer",
    "job_offer_close": "Job offer closed",
    "job_application": "Job application",
    "job_application_status_change": "Job application status change",
    "user_creation": "User creation",
  },
  "action_category": {
    "job_offers": "Job offers",
    "job_applications": "Job applications",
    "user_management": "User management"
  },
  "detail_field": {
    "granted_role": "Granted role",
    "job_title": "Job title",
    "reason": "Reason",
    "comment": "Comment",
    "status": "Status",
  },
  "detail_custom_field_enum_value": {
    "granted_role": {
      "admin": "Administrator",
      "user": "User"
    },
    "status": {
      "pending": "Pending",
      "approved": "Approved",
      "rejected": "Rejected"
    }
  },
  "source_field": {
    "application": "Application",
    "application_version": "Application version",
    "job_board": "Job board",
  },
  "resource_type": {
    "user": "User",
    "job_offer": "Job offer",
    "applicant": "Candidate"
  },
  "resource_custom_field": {},
  "actor_type": {
    "applicant": "Candidate",
    "user": "User"
  },
  "actor_custom_field": {
    "email": "Email"
  },
  "attachment_type": {
    "resume": "Resume"
  },
  "tag_type": {
    "applicant": "Candidate"
  }
}
```

!!! note
    Auditize currently supports English and French.
