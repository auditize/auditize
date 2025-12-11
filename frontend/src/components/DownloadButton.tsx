import { ActionIcon, Tooltip } from "@mantine/core";
import type { ActionIconProps } from "@mantine/core";
import { IconDownload } from "@tabler/icons-react";

export function DownloadButton({
  href,
  download,
  tooltipLabel,
  iconProps,
}: {
  href: string;
  download: string;
  tooltipLabel: string;
  iconProps?: ActionIconProps;
}) {
  return (
    <Tooltip label={tooltipLabel} withArrow position="bottom">
      <ActionIcon
        component="a"
        href={href}
        download={download}
        target="_blank"
        variant="transparent"
        {...iconProps}
      >
        <IconDownload />
      </ActionIcon>
    </Tooltip>
  );
}
