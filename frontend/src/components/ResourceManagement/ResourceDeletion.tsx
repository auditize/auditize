import { Box, Button, Group, Modal, Text } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { useTranslation } from "react-i18next";

import { InlineErrorMessage } from "../InlineErrorMessage";

interface ResourceDeletionProps {
  message: React.ReactNode;
  opened: boolean;
  onDelete: () => Promise<any>;
  queryKeyForInvalidation: any[];
  onClose: () => void;
}

export function ResourceDeletion({
  message,
  opened,
  onDelete,
  queryKeyForInvalidation,
  onClose,
}: ResourceDeletionProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => onDelete(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeyForInvalidation });
      onClose();
    },
  });

  return (
    <Modal
      title={<Text fw={600}>{t("resource.delete.confirm.title")}</Text>}
      size="lg"
      padding="lg"
      opened={opened}
      onClose={onClose}
    >
      <div>
        <Box>
          <Text pb="sm">{message}</Text>
          <Group justify="center">
            <Button onClick={onClose} size="xs" variant="outline">
              {t("resource.delete.cancel")}
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
              size="xs"
              color="red"
            >
              {t("resource.delete.delete")}
            </Button>
          </Group>
          <InlineErrorMessage>
            {mutation.error &&
              t("common.error", { error: mutation.error.message })}
          </InlineErrorMessage>
        </Box>
      </div>
    </Modal>
  );
}
