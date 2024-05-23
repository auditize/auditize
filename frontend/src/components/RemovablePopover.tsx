import { Button, Popover } from "@mantine/core";
import { useEffect, useState } from "react";

export function RemovablePopover({
  title,
  opened,
  isSet,
  onChange,
  onRemove,
  children,
}: {
  title: string;
  opened: boolean;
  isSet: boolean;
  onChange: (opened: boolean) => void;
  onRemove: () => void;
  children: React.ReactNode;
}) {
  return (
    <Popover opened={opened} onChange={onChange}>
      <Popover.Target>
        <Button.Group>
          <Button
            variant={isSet ? "filled" : "outline"}
            onClick={() => onChange(!opened)}
          >
            {title}
          </Button>
          <Button variant="outline" onClick={onRemove}>
            X
          </Button>
        </Button.Group>
      </Popover.Target>
      <Popover.Dropdown>{children}</Popover.Dropdown>
    </Popover>
  );
}
