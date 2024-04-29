from auditize.accesscontrol.models import AccessRights, LogPermissions


def normalize_access_rights(rights: AccessRights) -> AccessRights:
    if rights.is_superadmin:
        # cleanup all specific permissions
        return AccessRights(is_superadmin=True)

    if rights.logs.read and rights.logs.write:
        # cleanup permissions on specific repositories
        return rights.model_copy(
            update={"logs": LogPermissions(read=True, write=True)}
        )

    if rights.logs.read:
        # cleanup read permissions on specific repositories
        return rights.model_copy(
            update={"logs": rights.logs.model_copy(
                update={"repos": {
                    repo_id: repo_perms.model_copy(update={"read": False})
                    for repo_id, repo_perms in rights.logs.repos.items()
                }}
            )}
        )

    if rights.logs.write:
        # cleanup write permissions on specific repositories
        return rights.model_copy(
            update={"logs": rights.logs.model_copy(
                update={"repos": {
                    repo_id: repo_perms.model_copy(update={"write": False})
                    for repo_id, repo_perms in rights.logs.repos.items()
                }}
            )}
        )

    return rights
