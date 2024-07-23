import { notifications } from "@mantine/notifications";
import { t } from "i18next";

export function notifySuccess(message: string) {
  notifications.show({
    message: message,
    color: "green",
  });
}

export function notifyError(message: string) {
  notifications.show({
    title: t("common.errorModalTitle"),
    message: message,
    color: "red",
    autoClose: false,
  });
}
