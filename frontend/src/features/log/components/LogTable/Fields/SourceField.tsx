import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import {
  useLogTranslator,
  useSourceFieldValueTranslator,
} from "@/features/log/components/LogTranslation";

import {
  getCustomField,
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function SourceField({
  log,
  fieldName,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  fieldName: string;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const fieldValueTranslator = useSourceFieldValueTranslator(repoId);
  const field = getCustomField(log.source, fieldName);
  if (!field) {
    return null;
  }

  return (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.sourceField", {
        field: logTranslator("source_field", field.name).toLowerCase(),
      })}
      onClick={() =>
        onTableSearchParamChange("source", new Map([[field.name, field.value]]))
      }
    >
      {fieldValueTranslator(field)}
    </InlineSearchParamLink>
  );
}
