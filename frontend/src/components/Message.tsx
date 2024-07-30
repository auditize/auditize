import { Alert, Text, TextProps } from "@mantine/core";
import {
  IconAlertTriangle,
  IconCheckbox,
  IconInfoSquare,
} from "@tabler/icons-react";
import React from "react";

interface MessageProps {
  title?: string;
  textProps?: TextProps;
  children: React.ReactNode;
}

export function Message({
  color,
  icon,
  title,
  textProps,
  children,
}: {
  color: string;
  icon: React.ReactNode;
  title?: string;
  textProps?: TextProps;
  children: React.ReactNode;
}) {
  return (
    <Alert title={title} variant="light" color={color} icon={icon}>
      <Text size="sm" {...textProps}>
        {children}
      </Text>
    </Alert>
  );
}

export default Message;

function MessageSuccess({ title, textProps, children }: MessageProps) {
  return (
    <Message
      color="green"
      icon={<IconCheckbox />}
      title={title}
      textProps={textProps}
      children={children}
    />
  );
}

Message.Success = MessageSuccess;

function MessageInfo({ title, textProps, children }: MessageProps) {
  return (
    <Message
      color="blue"
      icon={<IconInfoSquare />}
      title={title}
      textProps={textProps}
      children={children}
    />
  );
}

Message.Info = MessageInfo;

function MessageWarning({ title, textProps, children }: MessageProps) {
  return (
    <Message
      color="orange"
      icon={<IconAlertTriangle />}
      title={title}
      textProps={textProps}
      children={children}
    />
  );
}

Message.Warning = MessageWarning;
