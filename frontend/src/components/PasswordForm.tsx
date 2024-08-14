import { isNotEmpty, matchesField } from "@mantine/form";
import { useTranslation } from "react-i18next";

export function usePasswordValidation() {
  const { t } = useTranslation();

  return {
    password: isNotEmpty(t("common.passwordForm.password.required")),
    passwordConfirmation: matchesField(
      "password",
      t("common.passwordForm.passwordConfirmation.doesNotMatch"),
    ),
  };
}
