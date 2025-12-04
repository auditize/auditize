import { Anchor, AnchorProps, Tooltip } from "@mantine/core";
import React from "react";
import { useTranslation } from "react-i18next";

import { CustomField } from "@/features/log/api";

export type TableSearchParamChangeHandler = (
  name: string,
  value: string | Map<string, string>,
) => void;

export function InlineSearchParamLink({
  label,
  onClick,
  children,
  anchorProps,
}: {
  label?: string;
  onClick: () => void;
  children: React.ReactNode;
  anchorProps?: AnchorProps;
}) {
  const { t } = useTranslation();

  return (
    <Tooltip
      label={t("log.inlineFilter.filterOn", { field: label })}
      disabled={!label}
      withArrow
      withinPortal={false}
    >
      <Anchor
        onClick={(event) => {
          event.stopPropagation();
          onClick();
        }}
        underline="hover"
        component="span"
        size="sm"
        {...anchorProps}
      >
        {children}
      </Anchor>
    </Tooltip>
  );
}

export function getCustomField(
  fields: CustomField[] | undefined,
  fieldName: string,
): CustomField | undefined {
  if (!fields) {
    return undefined;
  }
  return fields.find((f) => f.name === fieldName);
}

export function getCustomFieldValue(
  fields: CustomField[] | undefined,
  fieldName: string,
): string | null {
  const field = getCustomField(fields, fieldName);
  return field ? field.value : null;
}
