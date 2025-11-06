import {
  CheckIcon,
  Combobox,
  ComboboxItem,
  ComboboxItemGroup,
  ComboboxProps,
  Group,
  ScrollArea,
  useCombobox,
} from "@mantine/core";
import React, { useRef } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

function wordMatches(value: string, search: string) {
  return search
    .split(" ")
    .every((word) =>
      word.trim()
        ? value.toLowerCase().includes(word.trim().toLowerCase())
        : true,
    );
}

function buildComboboxOptions(
  data: ComboboxItemGroup<ComboboxItem>[],
  selected: string[],
  search: string,
) {
  const { t } = useTranslation();
  const isVisible = (
    group: ComboboxItemGroup<ComboboxItem>,
    item: ComboboxItem,
  ) =>
    !item.disabled
      ? search
        ? wordMatches(group.group, search) || wordMatches(item.label, search)
        : true
      : false;

  const optionGroups = data
    .filter((group) => group.items.some((item) => isVisible(group, item)))
    .map((group) => (
      <Combobox.Group key={group.group} label={group.group}>
        {group.items
          .filter((item) => isVisible(group, item))
          .map((item) => (
            <Combobox.Option
              key={item.value}
              value={item.value}
              disabled={item.disabled}
            >
              <Group gap="sm">
                {selected.includes(item.value) ? <CheckIcon size={12} /> : null}
                <span>{item.label}</span>
              </Group>
            </Combobox.Option>
          ))}
      </Combobox.Group>
    ));

  return (
    <>
      {optionGroups.length > 0 ? (
        optionGroups
      ) : (
        <Combobox.Empty>{t("common.noResults")}</Combobox.Empty>
      )}
    </>
  );
}

// This component is a replacement for `MultiSelect` because `MultiSelect` enforces
// a textinput with a summary of the selected values which is in our case:
// - not useful
// - problematic in terms of UI once two or more values have been selected
//
// Keep the function signature as close as possible to `MultiSelect`.
export function CustomMultiSelect({
  data,
  value,
  comboboxStore,
  onOptionSubmit,
  onRemove,
  closeOnSelect = false,
  children,
  footer,
  comboboxProps,
}: {
  data: ComboboxItemGroup<ComboboxItem>[];
  value: string[];
  comboboxStore: ReturnType<typeof useCombobox>;
  onOptionSubmit: (value: string) => void;
  onRemove: (value: string) => void;
  closeOnSelect?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
  comboboxProps?: ComboboxProps;
}) {
  const { t } = useTranslation();
  const viewportRef = useRef<HTMLDivElement>(null);
  const [search, setSearch] = useState("");

  return (
    <Combobox
      store={comboboxStore}
      onOpen={() => {
        comboboxStore.focusSearchInput();
        viewportRef.current?.scrollTo({ top: 0 });
      }}
      onClose={() => setSearch("")}
      onOptionSubmit={(changed: string) => {
        if (value.includes(changed)) {
          onRemove(changed);
        } else {
          onOptionSubmit(changed);
        }
        if (closeOnSelect) {
          comboboxStore.closeDropdown();
        }
      }}
      withinPortal={false}
      width={250}
      shadow="md"
      {...comboboxProps}
    >
      <Combobox.DropdownTarget>{children}</Combobox.DropdownTarget>

      <Combobox.Dropdown>
        <Combobox.Search
          value={search}
          onChange={(event) => setSearch(event.currentTarget.value)}
          placeholder={t("common.CustomMultiSelect.filterFields")}
        />
        <Combobox.Options>
          <ScrollArea.Autosize viewportRef={viewportRef} type="hover" mah={200}>
            {buildComboboxOptions(data, value, search)}
          </ScrollArea.Autosize>
        </Combobox.Options>
        {footer && <Combobox.Footer>{footer}</Combobox.Footer>}
      </Combobox.Dropdown>
    </Combobox>
  );
}
