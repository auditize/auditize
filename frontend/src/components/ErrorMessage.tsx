import { Text } from "@mantine/core";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";

export function ErrorMessage({
  message,
}: {
  message: string | null | undefined;
}) {
  if (!message) {
    return null;
  }
  return (
    <Text c="red" p="xs">
      {message}
    </Text>
  );
}

export function ApiErrorMessage({ error }: { error: Error | null }) {
  const { t } = useTranslation();
  let message;

  if (!error) {
    return null;
  }

  if (error instanceof AxiosError) {
    if ((error.response?.data as any).localized_message) {
      message = t("common.error.details", {
        error: (error.response?.data as any).localized_message,
      });
    } else {
      const statusCode = error.response?.status;
      if (statusCode === 401 || statusCode === 403) {
        message = t(`common.error.${statusCode}`);
      }
    }
  }

  if (!message) {
    message = t("common.error.unexpected");
  }

  return <ErrorMessage message={message} />;
}
