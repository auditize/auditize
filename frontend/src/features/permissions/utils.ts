import camelcaseKeys from "camelcase-keys";
import snakecaseKeys from "snakecase-keys";

export function emptyPermissions(): Auditize.Permissions {
  return {
    isSuperadmin: false,
    logs: {
      read: false,
      write: false,
      repos: {},
    },
    entities: {
      repos: {
        read: false,
        write: false,
      },
      users: {
        read: false,
        write: false,
      },
      integrations: {
        read: false,
        write: false,
      },
    },
  };
}

// NB: the following functions are used to convert between camelCase and snake_case and taking into the `repos` key
// which is an object whose keys are not "names" but ids. Those must be left as is.

function snakecasePermissions(
  permissions: Record<string, any>,
): Record<string, any> {
  return Object.fromEntries(
    Object.entries(permissions).map(([key, value]) => {
      if (key === "isSuperadmin") {
        return ["is_superadmin", value];
      } else {
        return [key, value];
      }
    }),
  );
}

export function snakecaseResourceWithPermissions(
  resource: Record<string, any>,
): Record<string, any> {
  return {
    ...snakecaseKeys(resource, { deep: true }),
    permissions: resource.permissions
      ? snakecasePermissions(resource.permissions)
      : undefined,
  };
}

function camelcasePermissions(
  permissions: Record<string, any>,
): Record<string, any> {
  return Object.fromEntries(
    Object.entries(permissions).map(([key, value]) => {
      if (key === "is_superadmin") {
        return ["isSuperadmin", value];
      } else {
        return [key, value];
      }
    }),
  );
}

export function camelcaseResourceWithPermissions(
  resource: Record<string, any>,
): Record<string, any> {
  return {
    ...camelcaseKeys(resource, { deep: true }),
    permissions: camelcasePermissions(resource.permissions),
  };
}
