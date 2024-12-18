import {
  Box,
  Button,
  Flex,
  Group,
  LoadingOverlay,
  Modal,
  Space,
  Text,
} from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { FormEventHandler, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { ApiErrorMessage } from "../ErrorMessage";
import { ModalActionButtons } from "../ModalActionButtons";
import { ModalTitle } from "../ModalTitle";

interface ResourceEditorProps {
  title: string;
  opened: boolean;
  onClose: () => void;
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
  onClose,
  isLoading = false,
  onSubmit,
  disabledSaving = false,
  onSave,
  onSaveSuccess,
  queryKeyForInvalidation,
  children,
}: ResourceEditorProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => onSave(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeyForInvalidation });
      if (onSaveSuccess) {
        onSaveSuccess(data);
      } else {
        onClose();
      }
    },
  });

  useEffect(() => {
    if (!opened) {
      mutation.reset();
    }
  }, [opened]);

  return (
    <Modal
      title={<ModalTitle>{title}</ModalTitle>}
      size="lg"
      padding="lg"
      opened={opened}
      onClose={onClose}
    >
      <Box px={"lg"}>
        <LoadingOverlay visible={opened && (isLoading || mutation.isPending)} />
        <form onSubmit={onSubmit(() => mutation.mutate())}>
          {children}
          <Space h="xl" />
          <Flex justify="center" align="center">
            <ApiErrorMessage
              error={mutation.error}
              textProps={{ pt: "0", size: "sm" }}
            />
          </Flex>
          <ModalActionButtons
            validateButtonLabel={t("common.save")}
            onClose={onClose}
            closeOnly={disabledSaving}
          />
        </form>
      </Box>
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
  const { t } = useTranslation();
  const navigate = useNavigate();
  const handleClose = () => navigate(-1);

  return (
    <Modal
      title={<ModalTitle>{t("common.unexpectedError")}</ModalTitle>}
      size="lg"
      padding="lg"
      opened={true}
      onClose={handleClose}
    >
      <div>
        <Box>
          <Text pb="sm">{message}</Text>
          <Group justify="center">
            <Button onClick={handleClose}>{t("common.close")}</Button>
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
  // We use isFetching instead of isPending to avoid displaying obsolete data
  // in case the user re-edits a resource he just saved
  const resourceQuery = useQuery({
    queryKey: queryKeyForLoad,
    queryFn: queryFnForLoad,
    enabled: !!resourceId,
    staleTime: 0,
  });

  useEffect(() => {
    if (!resourceQuery.isFetching && resourceQuery.data) {
      onDataLoaded(resourceQuery.data);
    }
  }, [resourceQuery.data, resourceQuery.isFetching]);

  if (resourceQuery.error) {
    return <ErrorModal message={resourceQuery.error.message} />;
  } else {
    return (
      <ResourceEditor
        opened={!!resourceId}
        isLoading={resourceQuery.isFetching}
        {...props}
      />
    );
  }
}
