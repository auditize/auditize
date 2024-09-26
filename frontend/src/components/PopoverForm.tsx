import { Button, Popover, PopoverProps, Stack } from "@mantine/core";
import { IconChevronDown, IconChevronUp } from "@tabler/icons-react";
import { useState } from "react";

import { iconSize } from "@/utils/ui";

export function PopoverForm({
  title,
  children,
  isFilled,
  disabled,
  popoverProps,
}: {
  title: string;
  children: React.ReactNode;
  isFilled: boolean;
  disabled?: boolean;
  popoverProps?: PopoverProps;
}) {
  const [opened, setOpened] = useState(false);

  return (
    <Popover
      opened={opened}
      onClose={() => setOpened(false)} // close on click outside
      position="bottom"
      withArrow
      keepMounted={true}
      width="20rem"
      disabled={disabled}
      {...popoverProps}
    >
      <Popover.Target>
        <Button
          rightSection={
            opened ? (
              <IconChevronUp style={iconSize("1.15rem")} />
            ) : (
              <IconChevronDown style={iconSize("1.15rem")} />
            )
          }
          onClick={() => setOpened((opened_) => !opened_)}
          variant={isFilled ? "light" : "outline"}
          disabled={disabled}
        >
          {title}
        </Button>
      </Popover.Target>
      <Popover.Dropdown p="0">{children}</Popover.Dropdown>
    </Popover>
  );
}
