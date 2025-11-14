import { Input, TextInput, TextInputProps } from "@mantine/core";
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

  return (
    <TextInput
      value={value}
      onChange={(event) => onChange(event.currentTarget.value)}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          onSubmit();
        }
      }}
      rightSection={
        value ? (
          <Input.ClearButton onClick={() => onChange("")} />
        ) : (
          <IconSearch style={iconSize(22)} />
        )
      }
      placeholder={t("common.search")}
      {...props}
    />
  );
}
