import { Box, Text, Title } from "@mantine/core";

export function Section({
  title,
  children,
  ...props
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Box {...props}>
      <Text
        size="1rem"
        fw={600}
        p="0.5rem"
        style={{
          borderWidth: "0px 0px 1px 0px",
          borderStyle: "solid",
          borderColor: "var(--mantine-primary-color-filled)",
        }}
      >
        {title}
      </Text>
      {children}
    </Box>
  );
}
