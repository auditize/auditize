import { Anchor, Tooltip } from "@mantine/core";
import React from "react";
import { useTranslation } from "react-i18next";

import { CustomField } from "@/features/log/api";

export type TableSearchParamChangeHandler = (
  name: string,
  value: string | Map<string, string>,
) => void;

export function InlineSearchParamLink({
  fieldLabel,
  onClick,
  fontSize = "sm",
  fontWeight,
  color,
  children,
}: {
  fieldLabel?: string;
  onClick: () => void;
  fontSize?: string;
  fontWeight?: string | number;
  color?: string;
  children: React.ReactNode;
}) {
  const { t } = useTranslation();

  return (
    <Tooltip
      label={t("log.inlineFilter.filterOn", { field: fieldLabel })}
      disabled={!fieldLabel}
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
        size={fontSize}
        fw={fontWeight}
        c={color}
      >
        {children}
      </Anchor>
    </Tooltip>
  );
}

export function getCustomFieldValue(
  fields: CustomField[] | undefined,
  fieldName: string,
): string | null {
  if (!fields) {
    return null;
  }

  const field = fields.find((f) => f.name === fieldName);
  return field ? field.value : null;
}

