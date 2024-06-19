import { Box, Group, Text } from "@mantine/core";
import React from "react";

export function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Box mb="md">
      <Group
        gap="0px"
        style={{
          borderWidth: "0px 0px 1px 0px",
          borderStyle: "solid",
          borderColor: "var(--mantine-primary-color-filled)",
        }}
      >
        {icon}
        <Text size="1rem" fw={600} p="0.5rem">
          {title}
        </Text>
      </Group>
      {children}
    </Box>
  );
}