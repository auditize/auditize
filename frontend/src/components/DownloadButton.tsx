import { ActionIcon, Tooltip } from "@mantine/core";
import type { ActionIconProps } from "@mantine/core";
import { IconDownload, IconProps } from "@tabler/icons-react";

export function DownloadButton({
  href,
  download,
  tooltipLabel,
  actionIconProps,
  iconDownloadProps,
}: {
  href: string;
  download: string;
  tooltipLabel: string;
  actionIconProps?: ActionIconProps;
  iconDownloadProps?: IconProps;
}) {
  return (
    <Tooltip label={tooltipLabel} withArrow position="bottom">
      <ActionIcon
        component="a"
        href={href}
        download={download}
        target="_blank"
        variant="transparent"
        {...actionIconProps}
      >
        <IconDownload {...iconDownloadProps} />
      </ActionIcon>
    </Tooltip>
  );
}
