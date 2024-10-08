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
    <Stack gap="0" p="sm">
      <Combobox onOptionSubmit={onChange} withinPortal={false}>
        <Combobox.EventsTarget>
          <TextInput
            placeholder={placeholder}
            value={getLabelForValue(value)}
            onChange={(event) => onChange(event.currentTarget.value)}
            rightSectionPointerEvents="all"
            rightSection={
              <CloseButton
                onClick={() => onChange("")}
                style={{ display: value ? undefined : "none" }}
              />
            }
            readOnly
          />
        </Combobox.EventsTarget>
        <Combobox.Options mt={rem(10)}>
          <ScrollArea.Autosize type="hover" mah={200} scrollbarSize={4}>
            {data.map((option) => (
              <Combobox.Option
                key={option.value}
                value={option.value}
                active={option.value === value}
              >
                <Group gap="xs">
                  {/* TODO: add mantine style on CheckIcon */}
                  {option.value === value && <CheckIcon size={12} />}
                  <span>{option.label}</span>
                </Group>
              </Combobox.Option>
            ))}
          </ScrollArea.Autosize>
        </Combobox.Options>
      </Combobox>
    </Stack>
  );
}
