import { CloseButton, Input, TextInput } from "@mantine/core";
import { useTranslation } from "react-i18next";

import { LogSearchParams } from "@/features/log/LogSearchParams";

export function FullTextSearchParamField({
  searchParams,
  onChange,
}: {
  searchParams: LogSearchParams;
  onChange: (name: string, value: any) => void;
}) {
  const { t } = useTranslation();
  return (
    <TextInput
      value={searchParams.q}
      onChange={(event) => onChange("q", event.target.value)}
      rightSection={
        <Input.ClearButton
          onClick={() => onChange("q", "")}
          style={{ display: searchParams.q !== "" ? undefined : "none" }}
        />
      }
      placeholder={t("common.search")}
      inputSize="15"
    />
  );
}
