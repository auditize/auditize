import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import {
  useDetailFieldValueTranslator,
  useLogTranslator,
} from "@/features/log/components/LogTranslation";

import {
  getCustomField,
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
  const fieldValueTranslator = useDetailFieldValueTranslator(repoId);
  const field = getCustomField(log?.details, fieldName);
  if (!field) {
    return null;
  }

  return (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.detailField", {
        field: logTranslator("detail_field", field.name).toLowerCase(),
      })}
      onClick={() =>
        onTableSearchParamChange(
          "details",
          new Map([[field.name, field.value]]),
        )
      }
    >
      {fieldValueTranslator(field)}
    </InlineSearchParamLink>
  );
}
