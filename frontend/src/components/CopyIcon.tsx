import { ActionIcon, CopyButton, Tooltip } from "@mantine/core";
import { IconCheck, IconCopy } from "@tabler/icons-react";

import { iconSize } from "@/utils/ui";

export function CopyIcon({
  value,
  disabled,
}: {
  value: string;
  disabled?: boolean;
}) {
  // Took from an example in https://mantine.dev/core/copy-button/
  return (
    <CopyButton value={value} timeout={1000}>
      {({ copied, copy }) => (
        <Tooltip
          label={copied ? "Copied" : "Copy"}
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
