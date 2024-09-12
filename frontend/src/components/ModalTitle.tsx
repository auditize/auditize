import { Text } from "@mantine/core";

export function ModalTitle({ children }: { children: React.ReactNode }) {
  return (
    <Text fw={550} size="lg">
      {children}
    </Text>
  );
}
