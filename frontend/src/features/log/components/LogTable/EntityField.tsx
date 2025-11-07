import React from "react";
import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";

import {
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function EntityPathField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return log.entityPath
    .map<React.ReactNode>((entity) => (
      <InlineSearchParamLink
        fieldLabel={t("log.inlineFilter.field.entity")}
        onClick={() => onTableSearchParamChange("entityRef", entity.ref)}
        key={entity.ref}
      >
        {entity.name}
      </InlineSearchParamLink>
    ))
    .reduce((prev, curr) => [prev, " > ", curr]);
}
