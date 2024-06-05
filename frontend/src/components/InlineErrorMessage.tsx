import { Text } from "@mantine/core";

export function InlineErrorMessage({ children }: { children: any }) {
  if (!children) {
    return null;
  }
  return (
    <Text c="red" p="xs">
      {children}
    </Text>
  );
}
