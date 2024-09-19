import { ActionIcon, Box, Flex, Group, Text, Tooltip } from "@mantine/core";
import {
  IconLayoutNavbarCollapse,
  IconLayoutNavbarExpand,
} from "@tabler/icons-react";
import React from "react";
import { useTranslation } from "react-i18next";

import { iconBesideText } from "@/utils/ui";

export function Section({
  title,
  icon,
  children,
  rightSection,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  rightSection?: React.ReactNode;
}) {
  return (
    <Box mb="md">
      <Group
        style={{
          borderWidth: "0px 0px 1px 0px",
          borderStyle: "solid",
          borderColor: "var(--mantine-primary-color-filled)",
        }}
        mb="0.25rem"
      >
        <Flex w="100%" justify="space-between" align="center">
          <Group gap="0px">
            {icon}
            <Text size="1rem" fw={600} p="0.5rem" pl="0.25rem">
              {title}
            </Text>
          </Group>
          {rightSection}
        </Flex>
      </Group>
      {children}
    </Box>
  );
}

export function SectionExpand({
  expanded,
  toggle,
}: {
  expanded: boolean;
  toggle: () => void;
}) {
  const { t } = useTranslation();

  if (expanded) {
    return (
      <Tooltip
        label={t("common.lessDetails")}
        withArrow
        withinPortal={false}
        position="bottom"
      >
        <ActionIcon variant="transparent" onClick={toggle}>
          <IconLayoutNavbarExpand style={iconBesideText({ size: "22px" })} />
        </ActionIcon>
      </Tooltip>
    );
  } else {
    return (
      <Tooltip
        label={t("common.moreDetails")}
        withArrow
        withinPortal={false}
        position="bottom"
      >
        <ActionIcon variant="transparent" onClick={toggle}>
          <IconLayoutNavbarCollapse style={iconBesideText({ size: "22px" })} />
        </ActionIcon>
      </Tooltip>
    );
  }
}
