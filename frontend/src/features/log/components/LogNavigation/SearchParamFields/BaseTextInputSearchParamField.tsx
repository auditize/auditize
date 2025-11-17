import { useState } from "react";

import { SearchInput } from "@/components/SearchInput";

import { SearchParamFieldPopover } from "./SearchParamFieldPopover";
import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";

export function BaseTextInputSearchParamField({
  label,
  name,
  value,
  openedByDefault,
  onChange,
  onRemove,
  onSubmit,
}: {
  label: string;
  name: string;
  value: string;
  openedByDefault: boolean;
  onChange: (value: any) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
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
      <SearchInput
        placeholder={label}
        value={value}
        onChange={onChange}
        onSubmit={onSubmit}
        disableSearchIcon
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
