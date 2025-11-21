import { useTranslation } from "react-i18next";

import { titlize } from "@/utils/format";

import { BaseTextInputSearchParamField } from "./BaseTextInputSearchParamField";

export function CustomFieldSearchParamField({
  name,
  values,
  onChange,
  onRemove,
  onSubmit,
  openedByDefault,
}: {
  name: string;
  values: Map<string, string>;
  onChange: (values: Map<string, string>) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
  openedByDefault: boolean;
}) {
  const { t } = useTranslation();
  const [groupName, fieldName] = name.split(".");

  return (
    <BaseTextInputSearchParamField
      label={t(`log.${groupName}`) + ": " + titlize(fieldName)}
      name={name}
      value={values.get(fieldName) ?? ""}
      openedByDefault={openedByDefault}
      onChange={(value) => onChange(new Map([...values, [fieldName, value]]))}
      onRemove={onRemove}
      onSubmit={onSubmit}
    />
  );
}
