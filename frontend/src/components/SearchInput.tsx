import { TextInputProps } from "@mantine/core";
import { IconSearch } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { iconSize } from "@/utils/ui";

import { ClearableTextInput } from "./ClearableTextInput";

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
    <ClearableTextInput
      value={value}
      onChange={onChange}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          onSubmit();
        }
      }}
      rightSection={<IconSearch style={iconSize(22)} />}
      placeholder={t("common.search")}
      {...props}
    />
  );
}
