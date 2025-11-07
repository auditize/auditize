import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

import {
  getCustomFieldValue,
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function DetailField({
  log,
  repoId,
  fieldName,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  fieldName: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  if (!log.details) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.details, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.detailField", {
        field: logTranslator("detail_field", fieldName).toLowerCase(),
      })}
      onClick={() =>
        onTableSearchParamChange("details", new Map([[fieldName, fieldValue]]))
      }
    >
      {fieldValue}
    </InlineSearchParamLink>
  );
}
