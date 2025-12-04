import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { DetailFieldValue } from "@/features/log/components/CustomFieldValues";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

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
  const field = getCustomField(log?.details, fieldName);
  if (!field) {
    return null;
  }

  return (
    <InlineSearchParamLink
      label={t("log.inlineFilter.field.detailField", {
        field: logTranslator("detail_field", field.name).toLowerCase(),
      })}
      onClick={() =>
        onTableSearchParamChange(
          "details",
          new Map([[field.name, field.value]]),
        )
      }
    >
      <DetailFieldValue repoId={repoId} field={field} />
    </InlineSearchParamLink>
  );
}
