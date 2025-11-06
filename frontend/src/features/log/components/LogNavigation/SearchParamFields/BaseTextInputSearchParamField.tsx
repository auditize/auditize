import { TextInput } from "@mantine/core";
import { useState } from "react";

import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";
import { SearchParamFieldPopover } from "./SearchParamFieldPopover";

export function BaseTextInputSearchParamField({
  label,
  name,
  value,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  name: string;
  value: string;
  openedByDefault: boolean;
  onChange: (value: any) => void;
  onRemove: (name: string) => void;
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
      focusTrap={true}
    >
      <TextInput
        placeholder={label}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        p="sm"
        // If the label (and then the placeholder) contains the word "email" for instance,
        // a password manager will try to fill the input with an email address, which is not what we want.
        // Make a best effort to avoid this behavior
        // (see https://www.stefanjudis.com/snippets/turn-off-password-managers/).
        autoComplete="off"
        data-1p-ignore
        data-lpignore="true"
        data-form-type="other"
        data-bwignore
      />
    </SearchParamFieldPopover>
  );
}

