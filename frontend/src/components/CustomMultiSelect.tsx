import {
  Button,
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
            <Combobox.Option key={item.value} value={item.value}>
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

// keep the function signature as close as possible to `MultiSelect`
export function CustomMultiSelect({
  placeholder,
  data,
  value,
  onOptionSubmit,
  onRemove,
}: {
  placeholder: string;
  data: ComboboxItemGroup<ComboboxItem>[];
  value: string[];
  onOptionSubmit: (value: string) => void;
  onRemove: (value: string) => void;
}) {
  const combobox = useCombobox({});
  const handleOnOptionSubmit = (changed: string) => {
    if (value.includes(changed)) {
      onRemove(changed);
    } else {
      onOptionSubmit(changed);
    }
    combobox.closeDropdown();
  };

  return (
    <Combobox
      store={combobox}
      onOptionSubmit={handleOnOptionSubmit}
      withinPortal={false}
      width="max-content"
    >
      <Combobox.DropdownTarget>
        <Button onClick={() => combobox.toggleDropdown()}>{placeholder}</Button>
      </Combobox.DropdownTarget>

      <Combobox.Dropdown>
        <Combobox.Options>
          <ScrollArea.Autosize type="hover" mah={200}>
            {buildComboboxOptions(data, value)}
          </ScrollArea.Autosize>
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  );
}
