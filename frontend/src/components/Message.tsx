import { Alert, AlertProps, Text, TextProps } from "@mantine/core";
import {
  IconAlertTriangle,
  IconCheckbox,
  IconInfoSquare,
} from "@tabler/icons-react";
import React from "react";

interface MessageProps {
  title?: string;
  alertProps?: AlertProps;
  textProps?: TextProps;
  children: React.ReactNode;
}

export function Message({
  color,
  icon,
  title,
  alertProps,
  textProps,
  children,
}: {
  color?: string;
  icon: React.ReactNode;
  title?: string;
  alertProps?: AlertProps;
  textProps?: TextProps;
  children: React.ReactNode;
}) {
  return (
    <Alert
      title={title}
      variant="light"
      color={color}
      icon={icon}
      {...alertProps}
    >
      <Text size="sm" {...textProps}>
        {children}
      </Text>
    </Alert>
  );
}

export default Message;

function MessageSuccess({
  title,
  alertProps,
  textProps,
  children,
}: MessageProps) {
  return (
    <Message
      color="green"
      icon={<IconCheckbox />}
      title={title}
      alertProps={alertProps}
      textProps={textProps}
      children={children}
    />
  );
}

Message.Success = MessageSuccess;

function MessageInfo({ title, alertProps, textProps, children }: MessageProps) {
  return (
    <Message
      // Primary color
      icon={<IconInfoSquare />}
      title={title}
      alertProps={alertProps}
      textProps={textProps}
      children={children}
    />
  );
}

Message.Info = MessageInfo;

function MessageWarning({
  title,
  alertProps,
  textProps,
  children,
}: MessageProps) {
  return (
    <Message
      color="orange"
      icon={<IconAlertTriangle />}
      title={title}
      alertProps={alertProps}
      textProps={textProps}
      children={children}
    />
  );
}

Message.Warning = MessageWarning;
