import { Button, Group } from "@mantine/core";
import { useTranslation } from "react-i18next";

// This component must be used inside a form with a onSubmit handler
export function ModalActionButtons({
  validateButtonLabel,
  onClose,
  closeOnly = false,
  dangerous = false,
}: {
  validateButtonLabel: string;
  onClose: () => void;
  closeOnly?: boolean;
  dangerous?: boolean;
}) {
  const { t } = useTranslation();
  return (
    <Group justify="center">
      {closeOnly ? (
        <Button onClick={onClose}>{t("common.close")}</Button>
      ) : (
        <>
          <Button onClick={onClose} variant="default">
            {t("common.cancel")}
          </Button>
          <Button type="submit" color={dangerous ? "red" : "blue"}>
            {validateButtonLabel}
          </Button>
        </>
      )}
    </Group>
  );
}
