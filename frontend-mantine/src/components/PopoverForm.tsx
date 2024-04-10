import { useState } from 'react';
import { Button, Stack, Popover } from '@mantine/core';
import { IconChevronUp, IconChevronDown } from '@tabler/icons-react';
import { iconSize } from '@/utils/ui';

export function PopoverForm({ title, children, isFilled }: { title: string; children: React.ReactNode; isFilled: boolean; }) {
  const [opened, setOpened] = useState(false);

  return (
    <Popover
      opened={opened}
      onClose={() => setOpened(false)} // close on click outside
      position="bottom" withArrow keepMounted={true}>
      <Popover.Target>
        <Button
          rightSection={opened ?
            <IconChevronUp style={iconSize("1.15rem")} /> :
            <IconChevronDown style={iconSize("1.15rem")} />}
          onClick={() => setOpened((opened_) => !opened_)}
          variant={isFilled ? 'light' : 'outline'}>
          {title}
        </Button>
      </Popover.Target>
      <Popover.Dropdown>
        <Stack>
          {children}
        </Stack>
      </Popover.Dropdown>
    </Popover>
  );
}
