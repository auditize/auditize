import { Button, Popover, Stack } from "@mantine/core";
import { IconChevronDown, IconChevronUp } from "@tabler/icons-react";
import { useState } from "react";

import { iconSize } from "@/utils/ui";

// NB: this component is no longer used as time of writing
export function PopoverForm({
  title,
  children,
  isFilled,
}: {
  title: string;
  children: React.ReactNode;
  isFilled: boolean;
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
        >
          {title}
        </Button>
      </Popover.Target>
      <Popover.Dropdown>
        <Stack>{children}</Stack>
      </Popover.Dropdown>
    </Popover>
  );
}
