import { Switch } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";

import { SearchParamFieldPopover } from "./SearchParamFieldPopover";

export function BooleanSearchParamField({
  label,
  value,
  onChange,
  onRemove,
  openedByDefault,
}: {
  label: string;
  value: boolean | undefined;
  onChange: (value: boolean | undefined) => void;
  onRemove: () => void;
  openedByDefault?: boolean;
}) {
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={value !== undefined}
      onChange={toggle}
      onRemove={onRemove}
    >
      <Switch
        checked={value ?? false}
        onChange={(event) =>
          onChange(event.currentTarget.checked ? true : undefined)
        }
        label={label}
        p="sm"
      />
    </SearchParamFieldPopover>
  );
}
