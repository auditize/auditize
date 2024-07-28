import { Text } from "@mantine/core";

export function InlineErrorMessage({
  children,
}: {
  children: string | Error | null | undefined;
}) {
  if (!children) {
    return null;
  }
  return (
    <Text c="red" p="xs">
      {children instanceof Error ? children.message : children}
    </Text>
  );
}
