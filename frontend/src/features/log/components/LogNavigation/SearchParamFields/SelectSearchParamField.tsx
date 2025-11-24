import { useDisclosure } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { SelectWithoutDropdown } from "@/components/SelectWithoutDropdown";
import { LogSearchParams } from "@/features/log/LogSearchParams";

import { SearchParamFieldPopover } from "./SearchParamFieldPopover";
import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";

export function SelectSearchParamField({
  label,
  searchParams,
  searchParamName,
  items,
  itemsQueryKeyExtra,
  itemLabel,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  items: (repoId: string) => Promise<string[]>;
  itemsQueryKeyExtra?: string;
  itemLabel: (value: string) => string;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const { t } = useTranslation();
  const consolidatedDataQuery = useQuery({
    queryKey: [
      "logConsolidatedData",
      searchParamName,
      searchParams.repoId,
      itemsQueryKeyExtra,
    ],
    queryFn: () => items(searchParams.repoId),
    enabled: !!searchParams.repoId,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  const value = searchParams.get(searchParamName);

  useEffect(() => {
    // on repository change, reset the selected value if it's not in the new data
    if (
      consolidatedDataQuery.data &&
      value &&
      !consolidatedDataQuery.data.includes(value)
    ) {
      onChange(searchParamName, "");
    }
  }, [consolidatedDataQuery.data]);

  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(searchParamName)}
      onRemove={() => onRemove(searchParamName)}
      loading={consolidatedDataQuery.isPending}
    >
      <SelectWithoutDropdown
        data={
          consolidatedDataQuery.data
            ? consolidatedDataQuery.data.map((item) => ({
                label: itemLabel(item),
                value: item,
              }))
            : []
        }
        value={value}
        onChange={(value) => onChange(searchParamName, value)}
        placeholder={
          consolidatedDataQuery.error
            ? t("common.notCurrentlyAvailable")
            : consolidatedDataQuery.data &&
                consolidatedDataQuery.data.length > 0
              ? t("common.chooseAValue")
              : t("common.noData")
        }
      />
    </SearchParamFieldPopover>
  );
}
