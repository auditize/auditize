import { Button, Popover } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconChevronDown, IconChevronUp } from "@tabler/icons-react";

import { iconSize } from "@/utils/ui";

export function PopoverForm({
  title,
  children,
  isFilled,
  disabled,
}: {
  title: string;
  children: React.ReactNode;
  isFilled: boolean;
  disabled?: boolean;
}) {
  const [opened, { close, toggle }] = useDisclosure();

  return (
    <Popover
      opened={opened}
      onClose={close}
      position="bottom"
      withArrow
      keepMounted
      disabled={disabled}
      shadow="md"
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
          onClick={toggle}
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
