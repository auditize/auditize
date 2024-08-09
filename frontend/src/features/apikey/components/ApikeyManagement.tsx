import { useDocumentTitle } from "@mantine/hooks";
import { IconKey } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { PermissionSummary } from "@/features/permissions";

import { Apikey, getApikeys } from "../api";
import { ApikeyDeletion } from "./ApikeyDeletion";
import { ApikeyCreation, ApikeyEdition } from "./ApikeyEditor";

export function ApikeysManagement() {
  const { t } = useTranslation();
  const { currentUser } = useAuthenticatedUser();
  const readOnly = currentUser.permissions.management.apikeys.write === false;
  useDocumentTitle(t("apikey.list.title"));

  return (
    <ResourceManagement
      title={
        <>
          <IconKey />
          {t("apikey.list.title")}
        </>
      }
      name={t("apikey.apikey")}
      queryKey={(search, page) => ["apikeys", "list", search, page]}
      queryFn={(search, page) => () => getApikeys(search, page)}
      columnBuilders={[
        [t("apikey.list.column.name"), (apikey: Apikey) => apikey.name],
        [
          t("apikey.list.column.permissions"),
          (apikey: Apikey) => (
            <PermissionSummary permissions={apikey.permissions} />
          ),
        ],
      ]}
      resourceCreationComponentBuilder={
        readOnly
          ? undefined
          : (opened, onClose) => (
              <ApikeyCreation opened={opened} onClose={onClose} />
            )
      }
      resourceEditionComponentBuilder={(resourceId, onClose) => (
        <ApikeyEdition
          apikeyId={resourceId}
          onClose={onClose}
          readOnly={readOnly}
        />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) =>
        readOnly ? undefined : (
          <ApikeyDeletion apikey={resource} opened={opened} onClose={onClose} />
        )
      }
    />
  );
}
