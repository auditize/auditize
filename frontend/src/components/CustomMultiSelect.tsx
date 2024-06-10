import {
  CheckIcon,
  Combobox,
  ComboboxItem,
  ComboboxItemGroup,
  Group,
  ScrollArea,
  useCombobox,
} from "@mantine/core";

function buildComboboxOptions(
  data: ComboboxItemGroup<ComboboxItem>[],
  selected: string[],
) {
  return (
    <>
      {data.map((group) => (
        <Combobox.Group key={group.group} label={group.group}>
          {group.items.map((item) => (
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
      ))}
    </>
  );
}

// This component is a replacement for `MultiSelect` because it enforce a textinput
// with a summary of the selected values which is in our case:
// - not useful
// - be problematic in term of UI once two or more values are selected
//
// keep the function signature as close as possible to `MultiSelect`
export function CustomMultiSelect({
  data,
  value,
  comboboxStore,
  onOptionSubmit,
  onRemove,
  children,
  footer,
}: {
  data: ComboboxItemGroup<ComboboxItem>[];
  value: string[];
  comboboxStore: ReturnType<typeof useCombobox>;
  onOptionSubmit: (value: string) => void;
  onRemove: (value: string) => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  const handleOnOptionSubmit = (changed: string) => {
    if (value.includes(changed)) {
      onRemove(changed);
    } else {
      onOptionSubmit(changed);
    }
    comboboxStore.closeDropdown();
  };

  return (
    <Combobox
      store={comboboxStore}
      onOptionSubmit={handleOnOptionSubmit}
      withinPortal={false}
      width="max-content"
    >
      <Combobox.DropdownTarget>{children}</Combobox.DropdownTarget>

      <Combobox.Dropdown>
        <Combobox.Options>
          <ScrollArea.Autosize type="hover" mah={200}>
            {buildComboboxOptions(data, value)}
          </ScrollArea.Autosize>
        </Combobox.Options>
        {footer && <Combobox.Footer>{footer}</Combobox.Footer>}
      </Combobox.Dropdown>
    </Combobox>
  );
}
