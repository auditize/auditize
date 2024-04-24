import { iconSize } from "@/utils/ui";
import { ActionIcon, CopyButton, Tooltip } from "@mantine/core";
import { IconCheck, IconCopy } from "@tabler/icons-react";

export function CopyIcon({value}: {value: string}) {
  return (
    <CopyButton value={value} timeout={1000}>
      {({ copied, copy }) => (
        <Tooltip label={copied ? 'Copied' : 'Copy'} withArrow position="right">
          <ActionIcon color={copied ? 'teal' : 'gray'} variant="subtle" onClick={copy}>
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
