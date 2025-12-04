import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

import {
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function ActionField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    <>
      <InlineSearchParamLink
        fieldLabel={t("log.inlineFilter.field.actionType")}
        onClick={() => onTableSearchParamChange("actionType", log.action.type)}
      >
        {logTranslator("action_type", log.action.type)}
      </InlineSearchParamLink>
      <br />
      <InlineSearchParamLink
        fieldLabel={t("log.inlineFilter.field.actionCategory")}
        onClick={() =>
          onTableSearchParamChange("actionCategory", log.action.category)
        }
        color="gray"
        fontSize="xs"
      >
        {logTranslator("action_category", log.action.category)}
      </InlineSearchParamLink>
    </>
  );
}

export function ActionTypeField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.actionType")}
      onClick={() => onTableSearchParamChange("actionType", log.action.type)}
    >
      {logTranslator("action_type", log.action.type)}
    </InlineSearchParamLink>
  );
}

export function ActionCategoryField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.actionCategory")}
      onClick={() =>
        onTableSearchParamChange("actionCategory", log.action.category)
      }
    >
      {logTranslator("action_category", log.action.category)}
    </InlineSearchParamLink>
  );
}
