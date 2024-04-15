import { useForm, isNotEmpty } from '@mantine/form';
import { Modal, Box, TextInput, Group, Button } from '@mantine/core';
import { createRepo, updateRepo, getRepo } from '../api';
import { useNavigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

function useRepoForm(values: {name?: string}) {
  return useForm({
    initialValues: {
      name: '',
      ...values
    },
    validate: {
      name: isNotEmpty('Name is required')
    }
  });
}

function RepoEditor(
  {form, title, opened, onClose, onSave, error} :
  {form: ReturnType<typeof useRepoForm>, title: string, opened: boolean, onClose?: () => void, onSave: () => void, error: string}) {
  const navigate = useNavigate();
  if (! onClose)
    onClose = () => navigate(-1);

  return (
    <Modal
      title={title} size="lg" padding="lg"
      opened={opened}
      // onClose is called even when the modal is close when the "ESC" key is pressed,
      // if onClose has been set to navigate(-1), it triggers an undesired navigation
      onClose={() => opened && onClose()}
    >
      <div>
        <Box mb="md">
          <form onSubmit={form.onSubmit(onSave)}>
            <TextInput label="Name" placeholder="Name" data-autofocus {...form.getInputProps('name')}/>
            <Group justify="center">
              <Button onClick={onClose}>Cancel</Button>
              <Button type='submit' color="blue">Save</Button>
            </Group>
          </form>
          {error && <Box mt="md" color="red">{error}</Box>}
        </Box>
      </div>
    </Modal>
  );
}

export function RepoCreation({opened}: {opened?: boolean}) {
  const navigate = useNavigate();
  const form = useRepoForm({});
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => createRepo(form.values),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['repos']});
      navigate("/repos");
    },
    onError: (error) => {
      setError(error.message);
    }
  });
  const [error, setError] = useState<string>("");

  useEffect(() => {
    form.reset();
    setError("");
  }, [opened]);

  return (
    <RepoEditor form={form} title={"Create new log repository"} opened={!!opened} onSave={mutation.mutate} error={error}/>
  );
}

export function RepoEdition({repoId}: {repoId: string | null}) {
  const navigate = useNavigate();
  const form = useRepoForm({});
  const queryClient = useQueryClient();
  const { data, isPending, error } = useQuery({
    queryKey: ['repos', repoId],
    queryFn: async () => getRepo(repoId!),
    enabled: !!repoId
  });
  const mutation = useMutation({
    mutationFn: () => updateRepo(repoId!, {name: form.values.name}),
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['repos']});
      navigate(-1);
    },
    onError: (error) => {
      setErrorMessage(error.message);
    }
  });
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    if (!!repoId) {
      form.reset();
      if (data)
        form.setValues(data);
      setErrorMessage("");
    }
  }, [repoId, data]);

  if (isPending || error) {
    return null;
  }

  return (
    <RepoEditor
      form={form}
      title={`Edit '${data.name}' log repository`}
      opened={!!repoId}
      onSave={mutation.mutate}
      error={errorMessage}/
    >
  );
}