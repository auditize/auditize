import { Modal, Box, Group, Button } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

interface ResourceEditorProps {
  title: string;
  opened: boolean;
  form: UseFormReturnType<any>;
  onSave: () => Promise<any>;
  onSaveSuccess?: (data: any) => void;
  isSaved?: boolean;
  queryKeyForInvalidation: any[];
  children: React.ReactNode;
}

function ResourceEditor(
  { title, opened, form, onSave, onSaveSuccess, isSaved = false, queryKeyForInvalidation, children }:
  ResourceEditorProps
) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => onSave(),
    onSuccess: ((data) => {
      queryClient.invalidateQueries({ queryKey: queryKeyForInvalidation });
      if (onSaveSuccess)
        onSaveSuccess(data);
      else
        navigate(-1);
    }),
    onError: (error) => {
      setError(error.message);
    }
  });
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setError("");
  }, [opened, isSaved]);

  const onClose = () => navigate(-1);

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
          <form onSubmit={form.onSubmit(() => mutation.mutate())}>
            {children}
            <Group justify="center">
              {
                ! isSaved && (
                  <>
                    <Button onClick={onClose}>Cancel</Button>
                    <Button type='submit' color="blue">Save</Button>
                  </>
                )
              }
              {
                isSaved && (
                  <Button onClick={onClose}>Close</Button>
                )
              }
            </Group>
          </form>
          {error && <Box mt="md" color="red">{error}</Box>}
        </Box>
      </div>
    </Modal>
  );
}

export function ResourceCreation(props: ResourceEditorProps) {
  const { form, opened } = props;

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (<ResourceEditor {...props} />);
}

type ResourceEditionProps = Omit<ResourceEditorProps, "opened"> & {
  resourceId: string | null;
  queryKeyForLoad: any[];
  queryFnForLoad: () => Promise<any>;
}

export function ResourceEdition({resourceId, queryKeyForLoad, queryFnForLoad, ...props}: ResourceEditionProps) {
  const { form } = props;
  const { data, isPending, error } = useQuery({
    queryKey: queryKeyForLoad,
    queryFn: queryFnForLoad,
    enabled: !!resourceId
  });

  useEffect(() => {
    if (!!resourceId) {
      if (data)
        form.setValues(data);
    }
  }, [resourceId, data]);

  if (isPending || error) {
    return null;
  }

  return (<ResourceEditor opened={!!resourceId} {...props} />);
}
