import { Button, Group, Modal, Text } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { ModalTitle } from "@/components/ModalTitle";

import { getInfo } from "../api";

export function About({
  opened,
  onClose,
}: {
  opened: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const query = useQuery({
    queryKey: ["info"],
    queryFn: () => getInfo(),
  });

  return (
    <Modal
      title={<ModalTitle>{t("about.title")}</ModalTitle>}
      opened={opened}
      onClose={onClose}
      size="xs"
    >
      <Text size="sm">
        {t("about.auditizeVersion", {
          version: query.data ? query.data.auditizeVersion : "...",
        })}
      </Text>
      <Group justify="center" mt="md">
        <Button onClick={onClose}>{t("common.close")}</Button>
      </Group>
    </Modal>
  );
}
