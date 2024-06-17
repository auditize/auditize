import { Trans, useTranslation } from "react-i18next";

import { ResourceDeletion } from "@/components/ResourceManagement";

import { deleteLogI18nProfile, LogI18nProfile } from "../api";

export function LogI18nProfileDeletion({
  profile,
  opened,
  onClose,
}: {
  profile: LogI18nProfile;
  opened: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  return (
    <ResourceDeletion
      message={
        <Trans
          i18nKey="logi18nprofile.delete.confirm"
          values={{ name: profile.name }}
        >
          Do you confirm the deletion of the log translation profile
          <b>{profile.name}</b> ?
        </Trans>
      }
      opened={opened}
      onDelete={() => deleteLogI18nProfile(profile.id)}
      queryKeyForInvalidation={["logi18nprofiles"]}
      onClose={onClose}
    />
  );
}
