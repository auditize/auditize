import { Modal, Box, Group, Button, Text } from '@mantine/core';
import { deleteRepo } from '../api';
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function RepoDeletion({repo, opened, onClose}: {repo: Repo, opened: boolean, onClose: () => void}) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => deleteRepo(repo.id),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['repos']});
      onClose();
    }
  });

  return (
    <Modal
      title={"Confirm deletion"} size="lg" padding="lg"
      opened={opened} onClose={onClose}
    >
      <div>
        <Box mb="md">
          <Text>Do you confirm the deletion of log repository {repo.name} ?</Text>
          <Group justify="center">
            <Button onClick={onClose}>Cancel</Button>
            <Button onClick={() => mutation.mutate()} color="blue">Delete</Button>
          </Group>
        </Box>
      </div>
    </Modal>
  );
}
