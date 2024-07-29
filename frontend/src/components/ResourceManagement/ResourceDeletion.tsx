import { Box, Button, Group, LoadingOverlay, Modal, Text } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { useTranslation } from "react-i18next";

import { InlineErrorMessage } from "../InlineErrorMessage";
import { ModalActionButtons } from "../ModalActionButtons";
import { ModalTitle } from "../ModalTitle";

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
      title={<ModalTitle>{t("resource.delete.confirm.title")}</ModalTitle>}
      size="lg"
      padding="lg"
      opened={opened}
      onClose={onClose}
    >
      <div>
        <Box>
          <LoadingOverlay visible={mutation.isPending} />
          <Text pb="sm">{message}</Text>
          <form
            onSubmit={(e) => {
              mutation.mutate();
              e.preventDefault();
            }}
          >
            <ModalActionButtons
              validateButtonLabel={t("common.delete")}
              onClose={onClose}
              dangerous
            />
          </form>
          <InlineErrorMessage>
            {mutation.error &&
              t("common.error", { error: mutation.error.message })}
          </InlineErrorMessage>
        </Box>
      </div>
    </Modal>
  );
}
