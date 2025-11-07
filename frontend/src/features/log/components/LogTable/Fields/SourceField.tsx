import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

import {
  getCustomFieldValue,
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

  if (!log.source) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.source, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.sourceField", {
        field: logTranslator("source_field", fieldName).toLowerCase(),
      })}
      onClick={() =>
        onTableSearchParamChange("source", new Map([[fieldName, fieldValue]]))
      }
    >
      {fieldValue}
    </InlineSearchParamLink>
  );
}
