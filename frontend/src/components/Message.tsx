import { Alert, Text } from "@mantine/core";
import { IconCheckbox, IconInfoSquare } from "@tabler/icons-react";
import React from "react";

namespace Message {
  export function Success({
    title,
    children,
  }: {
    title?: string;
    children: React.ReactNode;
  }) {
    return (
      <Alert
        title={title}
        variant="light"
        color="green"
        icon={<IconCheckbox />}
      >
        <Text>{children}</Text>
      </Alert>
    );
  }

  export function Info({
    title,
    children,
  }: {
    title?: string;
    children: React.ReactNode;
  }) {
    return (
      <Alert
        title={title}
        variant="light"
        color="blue"
        icon={<IconInfoSquare />}
      >
        <Text>{children}</Text>
      </Alert>
    );
  }
}

export default Message;
