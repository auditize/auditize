import { useTranslation } from "react-i18next";

import { CustomFieldType } from "@/features/log/api";
import { useCustomFieldTypes } from "@/features/log/components/useLogFields";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { titlize } from "@/utils/format";

import { BaseTextInputSearchParamField } from "./BaseTextInputSearchParamField";
import { BooleanSearchParamField } from "./BooleanSearchParamField";
import { SelectSearchParamField } from "./SelectSearchParamField";

function booleanToString(value: boolean | undefined): string | undefined {
  return value === undefined ? undefined : value ? "true" : "false";
}

function stringToBoolean(value: string | undefined): boolean | undefined {
  return value === undefined ? undefined : value === "true" ? true : false;
}

export function CustomFieldSearchParamField({
  searchParams,
  searchParamName,
  enumValues,
  enumLabel,
  onChange,
  onRemove,
  onSubmit,
  openedByDefault,
}: {
  searchParams: LogSearchParams;
  searchParamName: string;
  enumValues: (repoId: string, fieldName: string) => Promise<string[]>;
  enumLabel: (value: string) => string;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
  openedByDefault: boolean;
}) {
  const { t } = useTranslation();
  const fieldTypes = useCustomFieldTypes(searchParams.repoId);
  const fieldType = fieldTypes[searchParamName] ?? CustomFieldType.String;
  const [groupName, fieldName] = searchParamName.split(".");
  const label = t(`log.${groupName}`) + ": " + titlize(fieldName);

  if (fieldType === CustomFieldType.Enum) {
    return (
      <SelectSearchParamField
        label={label}
        searchParams={searchParams}
        searchParamName={searchParamName}
        items={(repoId) => enumValues(repoId, fieldName)}
        itemLabel={enumLabel}
        onChange={onChange}
        onRemove={onRemove}
        openedByDefault={openedByDefault}
      />
    );
  } else if (fieldType === CustomFieldType.Boolean) {
    return (
      <BooleanSearchParamField
        label={label}
        value={stringToBoolean(searchParams.get(searchParamName))}
        onChange={(value) => onChange(searchParamName, booleanToString(value))}
        onRemove={() => onRemove(searchParamName)}
        openedByDefault={openedByDefault}
      />
    );
  } else {
    return (
      <BaseTextInputSearchParamField
        label={label}
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
