import { Text } from "@mantine/core";

export function CustomModalTitle({ children }: { children: React.ReactNode }) {
  return <Text fw={600}>{children}</Text>;
}
