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

export function useApiErrorMessageBuilder(): (
  error: Error,
  opts?: { raw: boolean },
) => string {
  const { t } = useTranslation();

  return (error: Error, { raw = false }: { raw?: boolean } = {}) => {
    if (error instanceof AxiosError) {
      const localizedMessage = (error.response?.data as any)?.localized_message;
      if (localizedMessage) {
        return raw
          ? localizedMessage
          : t("common.error.details", { error: localizedMessage });
      } else {
        const statusCode = error.response?.status;
        if (statusCode === 401 || statusCode === 403) {
          return t(`common.error.${statusCode}`);
        }
      }
    }

    return t("common.error.unexpected");
  };
}

export function ApiErrorMessage({ error }: { error: Error | null }) {
  const errorMessageBuilder = useApiErrorMessageBuilder();

  if (!error) {
    return null;
  }
  return <ErrorMessage message={errorMessageBuilder(error)} />;
}
