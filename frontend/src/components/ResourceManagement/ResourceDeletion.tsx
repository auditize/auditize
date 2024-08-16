import { Box, Flex, LoadingOverlay, Modal, Text } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { ApiErrorMessage } from "../ErrorMessage";
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

  useEffect(() => {
    if (!opened) {
      mutation.reset();
    }
  }, [opened]);

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
          <Flex justify="center" align="center">
            <ApiErrorMessage error={mutation.error} />
          </Flex>
        </Box>
      </div>
    </Modal>
  );
}
