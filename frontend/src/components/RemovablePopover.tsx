import { Button, CloseButton, Popover } from "@mantine/core";

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
        <Button
          onClick={() => onChange(!opened)}
          rightSection={
            <CloseButton
              onClick={onRemove}
              component="a" // a button cannot be a child of a button
              variant="transparent"
            />
          }
          variant={isSet ? "light" : "outline"}
        >
          {title}
        </Button>
      </Popover.Target>
      <Popover.Dropdown>{children}</Popover.Dropdown>
    </Popover>
  );
}
