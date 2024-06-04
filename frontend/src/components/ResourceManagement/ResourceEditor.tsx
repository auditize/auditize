import { Box, Button, Group, LoadingOverlay, Modal, Text } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { FormEventHandler, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { InlineErrorMessage } from "../InlineErrorMessage";

interface ResourceEditorProps {
  title: string;
  opened: boolean;
  isLoading?: boolean;
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
  isLoading = false,
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
      if (onSaveSuccess) {
        onSaveSuccess(data);
      } else {
        navigate(-1);
      }
    },
    onError: (error) => {
      setError("Error: " + error.message);
    },
  });
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setError("");
  }, [opened, disabledSaving]);

  const onClose = () => navigate(-1);

  return (
    <Modal
      title={<Text fw={600}>{title}</Text>}
      size="lg"
      padding="lg"
      opened={opened}
      // onClose is called even when the modal is close when the "ESC" key is pressed,
      // if onClose has been set to navigate(-1), it triggers an undesired navigation
      onClose={() => opened && onClose()}
    >
      <div>
        <Box px={"lg"}>
          <LoadingOverlay
            visible={opened && (isLoading || mutation.isPending)}
          />
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
          <InlineErrorMessage>{error}</InlineErrorMessage>
        </Box>
      </div>
    </Modal>
  );
}

export function ResourceCreation(props: ResourceEditorProps) {
  return <ResourceEditor {...props} />;
}

type ResourceEditionProps = Omit<
  ResourceEditorProps,
  "opened" | "isLoading"
> & {
  resourceId: string | null;
  queryKeyForLoad: any[];
  queryFnForLoad: () => Promise<any>;
  onDataLoaded: (data: any) => void;
};

function ErrorModal({ message }: { message: string }) {
  const navigate = useNavigate();
  const handleClose = () => navigate(-1);

  return (
    <Modal
      title={<Text fw={600}>An error occured</Text>}
      size="lg"
      padding="lg"
      opened={true}
      onClose={handleClose}
    >
      <div>
        <Box>
          <Text pb="sm">{message}</Text>
          <Group justify="center">
            <Button onClick={handleClose}>Close</Button>
          </Group>
        </Box>
      </div>
    </Modal>
  );
}

export function ResourceEdition({
  resourceId,
  queryKeyForLoad,
  queryFnForLoad,
  onDataLoaded,
  ...props
}: ResourceEditionProps) {
  // here we use isFetching instead of isPending to avoid displaying obsolete data
  // in case the user re-edits a resource he just saved
  const { data, isFetching, error } = useQuery({
    queryKey: queryKeyForLoad,
    queryFn: queryFnForLoad,
    enabled: !!resourceId,
    staleTime: 0,
  });

  useEffect(() => {
    if (!isFetching && data) {
      onDataLoaded(data);
    }
  }, [data, isFetching]);

  if (error) {
    return <ErrorModal message={error.message} />;
  } else {
    return (
      <ResourceEditor opened={!!resourceId} isLoading={isFetching} {...props} />
    );
  }
}
