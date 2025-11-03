import {
  CheckIcon,
  CloseButton,
  Combobox,
  Group,
  rem,
  ScrollArea,
  Stack,
  TextInput,
} from "@mantine/core";
import { useDebouncedCallback } from "@mantine/hooks";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const MIN_SEARCH_LENGTH = 2;

export function SearchableSelectWithoutDropdown({
  value,
  onChange,
  data,
  onSearchChange,
  opened,
}: {
  value: string;
  onChange: (value: string) => void;
  data: { value: string; label: string }[] | undefined;
  onSearchChange: (search: string) => void;
  opened: boolean;
}) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const handleDebouncedSearch = useDebouncedCallback(onSearchChange, 300);
  const handleSearchChange = (search: string) => {
    setSearch(search); // Update the form field directly.
    if (search.length >= MIN_SEARCH_LENGTH) {
      handleDebouncedSearch(search);
    } else {
      onSearchChange("");
    }
  };

  // Reset the search when the dropdown is closed.
  useEffect(() => {
    if (!opened) {
      handleSearchChange("");
    }
  }, [opened]);

  return (
    <Stack gap="0" p="sm">
      <Combobox
        onOptionSubmit={(newValue) =>
          onChange(newValue === value ? "" : newValue)
        }
        withinPortal={false}
      >
        <Combobox.EventsTarget>
          <TextInput
            value={search}
            onChange={(event) => handleSearchChange(event.currentTarget.value)}
            rightSection={
              <CloseButton
                onClick={() => handleSearchChange("")}
                style={{
                  display: search ? undefined : "none",
                }}
              />
            }
            autoFocus={!value}
          />
        </Combobox.EventsTarget>
        <Combobox.Options mt={rem(10)}>
          <ScrollArea.Autosize type="hover" mah={200} scrollbarSize={4}>
            {data && data.length > 0 ? (
              data.map((option) => (
                <Combobox.Option
                  key={option.value + option.label}
                  value={option.value}
                  active={option.value === value}
                >
                  <Group gap="xs">
                    {/* TODO: add mantine style on CheckIcon */}
                    {option.value === value && <CheckIcon size={12} />}
                    <span>{option.label}</span>
                  </Group>
                </Combobox.Option>
              ))
            ) : (
              <Combobox.Empty>
                {search.length >= MIN_SEARCH_LENGTH
                  ? data === undefined
                    ? t("common.searchInProgress")
                    : t("common.noResults")
                  : t("common.typeToSearch")}
              </Combobox.Empty>
            )}
          </ScrollArea.Autosize>
        </Combobox.Options>
      </Combobox>
    </Stack>
  );
}
