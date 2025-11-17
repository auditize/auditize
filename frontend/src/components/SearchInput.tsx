import { FocusTrap, Input, TextInput, TextInputProps } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconSearch } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { iconSize } from "@/utils/ui";

export function SearchInput({
  value,
  onChange,
  onSubmit,
  ...props
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
} & Omit<TextInputProps, "value" | "onChange" | "onKeyDown">) {
  const { t } = useTranslation();
  const [isFocused, { open: setFocusActive, close: setFocusInactive }] =
    useDisclosure(false);

  return (
    <FocusTrap active={isFocused}>
      <TextInput
        onFocus={setFocusActive}
        onBlur={setFocusInactive}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            onSubmit();
          }
        }}
        rightSection={
          value ? (
            <Input.ClearButton
              onClick={() => {
                onChange("");
                setFocusActive();
              }}
            />
          ) : (
            <IconSearch style={iconSize(22)} />
          )
        }
        placeholder={t("common.search")}
        {...props}
      />
    </FocusTrap>
  );
}
