import { NumberInput } from "@mantine/core";
import { useState } from "react";

import { SearchParamFieldPopover } from "./SearchParamFieldPopover";
import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";

export function NumberSearchParamField({
  label,
  name,
  allowDecimal,
  value,
  onChange,
  onRemove,
  onSubmit,
  openedByDefault,
}: {
  label: string;
  name: string;
  value: number;
  allowDecimal?: boolean;
  onChange: (name: string, value: number) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
  openedByDefault: boolean;
}) {
  const [opened, setOpened] = useState(openedByDefault);

  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={setOpened}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(name)}
      onRemove={() => onRemove(name)}
      focusTrap
    >
      <NumberInput
        placeholder={label}
        value={value}
        onChange={(value) => onChange(name, value as number)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            onSubmit();
          }
        }}
        allowDecimal={allowDecimal}
        m="sm"
      />
    </SearchParamFieldPopover>
  );
}
