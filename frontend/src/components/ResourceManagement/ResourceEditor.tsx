import { Box, Button, Group, Modal } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { FormEventHandler, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

interface ResourceEditorProps {
  title: string;
  opened: boolean;
  onSubmit: (handleSubmit: () => void) => FormEventHandler<HTMLFormElement>;
  disabledSaving?: boolean;
  onSave: () => Promise<any>;
  queryKeyForInvalidation: any[];
  onSaveSuccess?: (data: any) => void;
  children: React.ReactNode;
}

function ResourceEditor({
  title,
  opened,
  onSubmit,
  disabledSaving = false,
  onSave,
  onSaveSuccess,
  queryKeyForInvalidation,
  children,
}: ResourceEditorProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => onSave(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeyForInvalidation });
      if (onSaveSuccess) onSaveSuccess(data);
      else navigate(-1);
    },
    onError: (error) => {
      setError(error.message);
    },
  });
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setError("");
  }, [opened, disabledSaving]);

  const onClose = () => navigate(-1);

  return (
    <Modal
      title={title}
      size="lg"
      padding="lg"
      opened={opened}
      // onClose is called even when the modal is close when the "ESC" key is pressed,
      // if onClose has been set to navigate(-1), it triggers an undesired navigation
      onClose={() => opened && onClose()}
    >
      <div>
        <Box px={"lg"}>
          <form onSubmit={onSubmit(() => mutation.mutate())}>
            {children}
            <Group justify="center" pt="md">
              {!disabledSaving && (
                <>
                  <Button onClick={onClose}>Cancel</Button>
                  <Button type="submit" color="blue">
                    Save
                  </Button>
                </>
              )}
              {disabledSaving && <Button onClick={onClose}>Close</Button>}
            </Group>
          </form>
          {error && (
            <Box mt="md" color="red">
              {error}
            </Box>
          )}
        </Box>
      </div>
    </Modal>
  );
}

export function ResourceCreation(props: ResourceEditorProps) {
  return <ResourceEditor {...props} />;
}

type ResourceEditionProps = Omit<ResourceEditorProps, "opened"> & {
  resourceId: string | null;
  queryKeyForLoad: any[];
  queryFnForLoad: () => Promise<any>;
  onDataLoaded: (data: any) => void;
};

export function ResourceEdition({
  resourceId,
  queryKeyForLoad,
  queryFnForLoad,
  onDataLoaded,
  ...props
}: ResourceEditionProps) {
  const { data, isPending, error } = useQuery({
    queryKey: queryKeyForLoad,
    queryFn: queryFnForLoad,
    enabled: !!resourceId,
  });

  useEffect(() => {
    if (!!resourceId) {
      if (data) onDataLoaded(data);
    }
  }, [resourceId, data]);

  if (isPending || error) {
    return null;
  }

  return <ResourceEditor opened={!!resourceId} {...props} />;
}
