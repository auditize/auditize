import { Stack } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { CustomDateTimePicker } from "@/components";
import { LogSearchParams } from "@/features/log/LogSearchParams";

import { SearchParamFieldPopover } from "./SearchParamFieldPopover";
import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";

export function DateInterval({
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
  const [untilError, setUntilError] = useState<string | null>(null);
  const isIntervalValid = (since: Date | null, until: Date | null) =>
    !since || !until || since <= until;

  return (
    <SearchParamFieldPopover
      title={t("log.date")}
      removable={!FIXED_SEARCH_PARAM_NAMES.has("emittedAt")}
      onRemove={() => onRemove("emittedAt")}
      isSet={!!(searchParams.since || searchParams.until)}
      opened={opened}
      onChange={toggle}
    >
      <Stack p="sm" gap="sm">
        <CustomDateTimePicker
          placeholder={t("log.dateFrom")}
          value={searchParams.since}
          onChange={(since) => {
            onChange("since", since);
            setUntilError(
              isIntervalValid(since, searchParams.until)
                ? null
                : t("log.list.untilMustBeGreaterThanSince"),
            );
          }}
        />
        <CustomDateTimePicker
          placeholder={t("log.dateTo")}
          value={searchParams.until}
          onChange={(until) => {
            if (isIntervalValid(searchParams.since, until)) {
              onChange("until", until);
              setUntilError(null);
            } else {
              setUntilError(t("log.list.untilMustBeGreaterThanSince"));
            }
          }}
          initToEndOfDay
          dateTimePickerProps={{
            error: untilError ?? undefined,
            excludeDate: (until) =>
              !isIntervalValid(searchParams.since, new Date(until)),
          }}
        />
      </Stack>
    </SearchParamFieldPopover>
  );
}
