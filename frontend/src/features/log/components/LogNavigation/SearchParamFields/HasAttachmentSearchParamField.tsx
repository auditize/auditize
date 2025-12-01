import { useTranslation } from "react-i18next";

import { LogSearchParams } from "@/features/log/LogSearchParams";

import { BooleanSearchParamField } from "./BooleanSearchParamField";

export function HasAttachmentSearchParamField({
  searchParams,
  onChange,
  onRemove,
  openedByDefault,
}: {
  searchParams: LogSearchParams;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
  openedByDefault: boolean;
}) {
  const { t } = useTranslation();
  return (
    <BooleanSearchParamField
      label={t("log.hasAttachment")}
      value={searchParams.hasAttachment}
      onChange={(value) => onChange("hasAttachment", value)}
      onRemove={() => onRemove("hasAttachment")}
      openedByDefault={openedByDefault}
    />
  );
}
