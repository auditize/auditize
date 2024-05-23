import { Combobox, ScrollArea, TextInput } from "@mantine/core";

export function SelectWithoutDropdown({
  value,
  onChange,
  data,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  data: { value: string; label: string }[];
  placeholder: string;
}) {
  const getLabelForValue = (value: string) =>
    data.find((option) => option.value === value)?.label || value;

  return (
    <Combobox onOptionSubmit={onChange} withinPortal={false}>
      <Combobox.EventsTarget>
        <TextInput
          placeholder={placeholder}
          value={getLabelForValue(value)}
          onChange={(event) => onChange(event.currentTarget.value)}
        />
      </Combobox.EventsTarget>
      <Combobox.Options mt="sm">
        <ScrollArea.Autosize type="hover" mah={200} scrollbarSize={4}>
          {data.map((option) => (
            <Combobox.Option key={option.value} value={option.value}>
              {option.label}
            </Combobox.Option>
          ))}
        </ScrollArea.Autosize>
      </Combobox.Options>
    </Combobox>
  );
}
