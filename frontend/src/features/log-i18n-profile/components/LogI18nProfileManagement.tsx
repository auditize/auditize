import { useDocumentTitle } from "@mantine/hooks";
import { IconLanguage } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { humanizeDate } from "@/utils/date";
import { iconBesideText } from "@/utils/ui";

import { getLogI18nProfiles, LogI18nProfile } from "../api";
import { LogI18nProfileDeletion } from "./LogI18nProfileDeletion";
import {
  LogI18nProfileCreation,
  LogI18nProfileEdition,
} from "./LogI18nProfileEditor";

export function LogI18nProfileManagement() {
  const { currentUser } = useAuthenticatedUser();
  const { t } = useTranslation();
  const readOnly = currentUser.permissions.management.repos.write === false;
  useDocumentTitle(t("logi18nprofile.list.title"));

  return (
    <ResourceManagement
      title={
        <>
          <IconLanguage
            style={iconBesideText({
              size: "26",
              top: "4px",
              marginRight: "0.25rem",
            })}
          />
          {t("logi18nprofile.list.title")}
        </>
      }
      name={t("logi18nprofile.logi18nprofile")}
      queryKey={(search, page) => ["logi18nprofiles", "list", search, page]}
      queryFn={(search, page) => () => getLogI18nProfiles(search, page)}
      columnDefinitions={[
        [
          t("logi18nprofile.list.column.name"),
          (profile: LogI18nProfile) => profile.name,
        ],
        [
          t("logi18nprofile.list.column.langs"),
          (profile: LogI18nProfile) =>
            Object.entries(profile.translations)
              .map(([lang, _]) => t("language." + lang))
              .join(", "),
        ],
        [
          t("logi18nprofile.list.column.createdAt"),
          (profile: LogI18nProfile) => humanizeDate(profile.createdAt),
        ],
      ]}
      resourceCreationComponentBuilder={
        readOnly
          ? undefined
          : (opened, onClose) => (
              <LogI18nProfileCreation opened={opened} onClose={onClose} />
            )
      }
      resourceEditionComponentBuilder={(resourceId, onClose) => (
        <LogI18nProfileEdition
          profileId={resourceId}
          onClose={onClose}
          readOnly={readOnly}
        />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) =>
        readOnly ? undefined : (
          <LogI18nProfileDeletion
            profile={resource}
            opened={opened}
            onClose={onClose}
          />
        )
      }
    />
  );
}
