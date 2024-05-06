import { Box, Button, Group, Modal, Text } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";

interface ResourceDeletionProps {
  title: string;
  message: string;
  opened: boolean;
  onDelete: () => Promise<any>;
  queryKeyForInvalidation: any[];
  onClose: () => void;
}

export function ResourceDeletion({
  title,
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
      title={title}
      size="lg"
      padding="lg"
      opened={opened}
      onClose={onClose}
    >
      <div>
        <Box mb="md">
          <Text>{message}</Text>
          <Group justify="center">
            <Button onClick={onClose}>Cancel</Button>
            <Button onClick={() => mutation.mutate()} color="blue">
              Delete
            </Button>
          </Group>
        </Box>
      </div>
    </Modal>
  );
}
