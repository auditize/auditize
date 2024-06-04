import { Box, Button, Group, Modal, Text } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import React from "react";

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
      title={<Text fw={600}>Confirm Deletion</Text>}
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
              Cancel
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
              size="xs"
              color="red"
            >
              Delete
            </Button>
          </Group>
          <InlineErrorMessage>
            {mutation.error && "Error: " + mutation.error.message}
          </InlineErrorMessage>
        </Box>
      </div>
    </Modal>
  );
}
