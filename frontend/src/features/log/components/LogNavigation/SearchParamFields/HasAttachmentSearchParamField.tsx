import { Switch } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useTranslation } from "react-i18next";

import { LogSearchParams } from "@/features/log/LogSearchParams";
import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";
import { SearchParamFieldPopover } from "./SearchParamFieldPopover";

export function HasAttachmentSearchParamField({
  searchParams,
  openedByDefault,
  onChange,
  onRemove,
}: {
  searchParams: LogSearchParams;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const { t } = useTranslation();
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={t("log.hasAttachment")}
      opened={opened}
      isSet={searchParams.hasAttachment !== undefined}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has("hasAttachment")}
      onRemove={() => onRemove("hasAttachment")}
    >
      <Switch
        checked={searchParams.hasAttachment ?? false}
        onChange={(event) =>
          onChange(
            "hasAttachment",
            event.currentTarget.checked ? true : undefined,
          )
        }
        label={t("log.hasAttachment")}
        p="sm"
      />
    </SearchParamFieldPopover>
  );
}

