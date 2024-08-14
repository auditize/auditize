import { hasLength, isNotEmpty, matchesField } from "@mantine/form";
import { useTranslation } from "react-i18next";

function combineValidators(...validators: ((value: string) => any)[]) {
  return (value: string) => {
    for (const validator of validators) {
      const error = validator(value);
      if (error) {
        return error;
      }
    }

    return null;
  };
}

export function usePasswordValidation() {
  const { t } = useTranslation();

  return {
    password: combineValidators(
      isNotEmpty(t("common.passwordForm.password.required")),
      hasLength(
        { min: 8 },
        t("common.passwordForm.password.tooShort", { min: 8 }),
      ),
    ),
    passwordConfirmation: matchesField(
      "password",
      t("common.passwordForm.passwordConfirmation.doesNotMatch"),
    ),
  };
}
