import { ActionIcon, Anchor, Text, Tooltip, useCombobox } from "@mantine/core";
import { IconColumns3 } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { useLogNavigationState } from "@/features/log/components/LogNavigation";
import { useColumnFields } from "@/features/log/components/useLogFields";

export function ColumnSelector({
  repoId,
  selected,
  onColumnAdded,
  onColumnRemoved,
  onColumnReset,
}: {
  repoId: string;
  selected: Array<string>;
  onColumnAdded: (name: string) => void;
  onColumnRemoved: (name: string) => void;
  onColumnReset: () => void;
}) {
  const { t } = useTranslation();
  const { fields, loading: fieldsLoading } = useColumnFields(repoId);
  const comboboxStore = useCombobox();
  const { logComponentRef } = useLogNavigationState();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={fields}
      value={Array.from(selected)}
      onOptionSubmit={onColumnAdded}
      onRemove={onColumnRemoved}
      footer={
        <Anchor onClick={onColumnReset}>
          <Text size="xs">{t("log.list.columnSelector.reset")}</Text>
        </Anchor>
      }
      comboboxProps={{
        withinPortal: true,
        portalProps: { target: logComponentRef.current! },
        position: "bottom-end",
      }}
    >
      <Tooltip
        label={t("log.list.columnSelector.tooltip")}
        disabled={comboboxStore.dropdownOpened}
        position="bottom-end"
        withArrow
        withinPortal={false}
      >
        <ActionIcon
          onClick={() => comboboxStore.toggleDropdown()}
          loading={fieldsLoading}
          loaderProps={{ type: "dots" }}
          variant="transparent"
        >
          <IconColumns3 />
        </ActionIcon>
      </Tooltip>
    </CustomMultiSelect>
  );
}
