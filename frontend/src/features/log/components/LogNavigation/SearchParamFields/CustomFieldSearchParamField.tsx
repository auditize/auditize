import { useTranslation } from "react-i18next";

import { CustomFieldType } from "@/features/log/api";
import { useCustomFieldTypes } from "@/features/log/components/useLogFields";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { titlize } from "@/utils/format";

import { BaseTextInputSearchParamField } from "./BaseTextInputSearchParamField";
import { SelectSearchParamField } from "./SelectSearchParamField";

export function CustomFieldSearchParamField({
  searchParams,
  searchParamName,
  enumValues,
  onChange,
  onRemove,
  onSubmit,
  openedByDefault,
}: {
  searchParams: LogSearchParams;
  searchParamName: string;
  enumValues: (repoId: string, fieldName: string) => Promise<string[]>;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
  openedByDefault: boolean;
}) {
  const { t } = useTranslation();
  const fieldTypes = useCustomFieldTypes(searchParams.repoId);
  const fieldType = fieldTypes[searchParamName] ?? CustomFieldType.String;
  const [groupName, fieldName] = searchParamName.split(".");

  if (fieldType === CustomFieldType.Enum) {
    return (
      <SelectSearchParamField
        label={t(`log.${groupName}`) + ": " + titlize(fieldName)}
        searchParams={searchParams}
        searchParamName={searchParamName}
        items={(repoId) => enumValues(repoId, fieldName)}
        itemLabel={(value) => titlize(value)}
        onChange={onChange}
        onRemove={onRemove}
        openedByDefault={openedByDefault}
      />
    );
  } else {
    return (
      <BaseTextInputSearchParamField
        label={t(`log.${groupName}`) + ": " + titlize(fieldName)}
        name={searchParamName}
        value={searchParams.get(searchParamName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) => onChange(searchParamName, value)}
        onRemove={onRemove}
        onSubmit={onSubmit}
      />
    );
  }
}
