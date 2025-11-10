import { useDisclosure } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { SearchableSelectWithoutDropdown } from "@/components/SearchableSelectWithoutDropdown";
import { NameRefPair } from "@/features/log/api";
import { LogSearchParams } from "@/features/log/LogSearchParams";

import { SearchParamFieldPopover } from "./SearchParamFieldPopover";
import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";

export function SearchableSearchParamField({
  label,
  searchParams,
  searchParamName,
  items,
  itemLabel,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  items: (repoId: string, query: string) => Promise<NameRefPair[]>;
  itemLabel: (repoId: string, value: string) => Promise<string>;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const [search, setSearch] = useState("");
  const searchQuery = useQuery({
    queryKey: ["logFieldNames", searchParamName, searchParams.repoId, search],
    queryFn: () => items(searchParams.repoId, search),
    enabled: !!searchParams.repoId && !!search,
  });
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;
  const labelQuery = useQuery({
    queryKey: [
      "logFieldNameFromRef",
      searchParamName,
      searchParams.repoId,
      value,
    ],
    queryFn: () => itemLabel(searchParams.repoId, value),
    enabled: !!searchParams.repoId && !!value,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);

  // On repository change, reset the selected value if a corresponding
  // label cannot be found.
  useEffect(() => {
    if (value && labelQuery.data === "") {
      onChange(searchParamName, "");
    }
  }, [labelQuery.data]);

  // Build the available options from the search query if any (example: the user is performing a search)
  // or from the label query if any (example: the page is loaded with the selected value already in the URL).
  const data =
    searchQuery.isEnabled && searchQuery.data
      ? searchQuery.data.map((item) => ({
          label: item.name,
          value: item.ref,
        }))
      : labelQuery.isEnabled && labelQuery.data
        ? [
            {
              label: labelQuery.data,
              value: value,
            },
          ]
        : undefined;

  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(searchParamName)}
      onRemove={() => onRemove(searchParamName)}
      loading={searchQuery.isEnabled && searchQuery.isPending}
      focusTrap
    >
      <SearchableSelectWithoutDropdown
        data={data}
        value={value}
        onChange={(value) => onChange(searchParamName, value)}
        onSearchChange={setSearch}
        opened={opened}
      />
    </SearchParamFieldPopover>
  );
}
