# Concepts

## Log Repositories

Log Repositories (also named "Repositories" or "Repos") are log containers. Each Log Repository is associated to a dedicated MongoDB database providing strong isolation between logs. Log Repositories allow you to set up specific permissions and settings (such as a retention period or status).

You can configure:

- Retention period: the time after which logs are automatically deleted
- Status:
    - Enabled: logs can be send and viewed
    - Read-only: logs can only be viewed
    - Disabled: logs cannot be viewed nor sent
- Log i18n Profile: the profile used to translate logs in the web interface

## Log i18n Profiles

Auditize supports internationalization of the web interface but also of the logs themselves. The internationalization of logs is done through Log i18n Profiles. Log i18n Profiles let you upload translation files for the languages you want to support (and are supported by Auditize).
The log translation applies to log fields whose value is considered to be a key. Here are the log fields that can be translated:

- `action_type`
- `action_category`
- `actor_type`
- `actor_custom_field` (custom field names of the actor)
- `source_field` (field names within the source)
- `detail_field` (field names within the details)
- `resource_type`
- `resource_custom_field` (custom field names of the resource)
- `tag_type`
- `attachment_type`

Example of a translation file:

```json
{
  "action_type": {
    "job-offer-creation": "New job offer",
    "job-offer-close": "Job offer closed",
    "job-application": "Job application",
    "job-application-status-change": "Job application status change",
    "user-creation": "User creation",
  },
  "action_category": {
    "job-offers": "Job offers",
    "job-applications": "Job applications",
    "users": "Users"
  },
  "detail_field": {
    "granted-role": "Granted role",
    "job-title": "Job title",
    "reason": "Reason",
    "comment": "Comment",
    "status": "Status",
  },
  "source_field": {
    "application": "Application",
    "application-version": "Application version",
    "job-board": "Job board",
  },
  "resource_type": {
    "user": "User",
    "job-offer": "Job offer",
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


## Users

Users access Auditize through the web interface. If you want to use the REST API, you can use [API keys](#api-keys).
When a user is created, he'll receive an email with a link to set his password. Once the password has been chosen, he will be able to log in to the web interface. Permissions can be set on a user, please refer to the [Permissions](#permissions) section.

!!! note
    You'll notice that the certain permissions or combination of permissions does not seem to make sense for a user. For instance:
    
    - a user with the "write" permission on the logs of a repository (while it's not possible to "push" logs through the web interface)
    - a user with the "write" permission on the ressource management without the corresponding "read" permission

    This is because the permissions are also used for API keys and also because these permissions also used to 
    determine what permissions a [user can grant to other users](#granting-permissions).


## API keys

API keys are used to access Auditize programmatically through the REST API. Like [Users](#users), API keys have a set of [Permissions](#permissions). When a new API key is created, a secret is generated and only shown once. If you lose the secret or want to generate a new one, you can generate a new secret for an existing API key. In that case, the former secret will no longer be valid.

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

To each of these resources, you can set the following permissions:

- Read: it allows the user to view the resource
- Write: it allows the user to alter or delete the resource


### Log permissions

Log permissions control the access to logs. Permissions can be set either globally or per repository.

- the "Read" permission allows the user to view logs
- the "Write" permission allows the user to send logs to the Auditize API

When log permissions are set per repository, you can also restrict the read permission to certain log entities. When no log entity is selected, the permission applies to all logs independently of their associated entity. If log entities are selected, the user / API key will only be able to view logs associated with the selected entities.


### Superadmin role

When a user is granted the Superadmin role, he has all permissions on all resources and logs.

!!! warning
    The Superadmin role should be granted with caution and be limited to a small number of users. Setting fine grained permissions to users is recommended.


### Granting permissions

When a user has the permission to manage Users or API keys ("write" permission), the permissions he is allowed to grant are the ones he has himself. For example, if a user has the "read" permission on the logs of a given repository, he can only grant the "read" permission to other users on the same repository.

Please note that you'll need a "read" permission on a repository's logs without entity restrictions to grant the "read" permission (with or without entity restrictions) to other users to this repository's logs.


### Permissions normalization

When saving permissions, they are normalized to ensure consistency and avoid possible side effects in future permissions updates. The normalization process is as follows:

- if a user has the "read" log permission globally (on all repositories), any "read" permission granted on a specific repository and any log entity restrictions are removed
- if a user has the "write" log permission globally (on all repositories), any "write" permission granted on a specific repository is removed
- if a user has the superadmin role, all other permissions are removed
