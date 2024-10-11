import { ActionIcon, CopyButton, Tooltip } from "@mantine/core";
import { IconCheck, IconCopy } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { iconSize } from "@/utils/ui";

export function CopyIcon({
  value,
  disabled,
}: {
  value: string;
  disabled?: boolean;
}) {
  const { t } = useTranslation();

  // Based on an example in https://mantine.dev/core/copy-button/
  return (
    <CopyButton value={value} timeout={1000}>
      {({ copied, copy }) => (
        <Tooltip
          label={copied ? t("common.copied") : t("common.copy")}
          withArrow
          position="right"
          disabled={disabled}
        >
          <ActionIcon
            color={copied ? "teal" : "gray"}
            variant="subtle"
            onClick={copy}
            disabled={disabled}
          >
            {copied ? (
              <IconCheck style={iconSize(16)} />
            ) : (
              <IconCopy style={iconSize(16)} />
            )}
          </ActionIcon>
        </Tooltip>
      )}
    </CopyButton>
  );
}
