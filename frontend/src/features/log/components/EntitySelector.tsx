import {
  ActionIcon,
  Anchor,
  Box,
  Button,
  Checkbox,
  Group,
  Loader,
  RenderTreeNodePayload,
  ScrollArea,
  Space,
  Stack,
  Text,
  Tree,
  TreeNodeData,
  useTree,
  UseTreeReturnType,
} from "@mantine/core";
import { IconChevronDown, IconChevronRight } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { PopoverForm } from "@/components/PopoverForm";
import { iconSize } from "@/utils/ui";

import { getAllLogEntities, getLogEntity, LogEntity } from "../api";

function findNode(
  nodes: TreeNodeData[],
  nodeValue: string,
): TreeNodeData | null {
  for (const node of nodes) {
    if (node.value === nodeValue) {
      return node;
    }
    if (node.children) {
      const found = findNode(node.children, nodeValue);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

function hasAnyChildNodeChecked(node: TreeNodeData, checkNodeValues: string[]) {
  if (checkNodeValues.includes(node.value)) {
    return true;
  }
  if (node.children) {
    for (const child of node.children) {
      if (hasAnyChildNodeChecked(child, checkNodeValues)) {
        return true;
      }
    }
  }
  return false;
}

async function getLogEntitySiblings(
  repoId: string,
  entityRef: string,
): Promise<LogEntity[]> {
  const entity = await getLogEntity(repoId, entityRef);
  return getAllLogEntities(repoId, entity.parentEntityRef);
}

function logEntityToTreeNodeData(entity: LogEntity): TreeNodeData {
  return {
    value: entity.ref,
    label: entity.name,
    // An empty array means that the node has children, but they have not been loaded yet
    children: entity.hasChildren ? [] : undefined,
  };
}

async function completeTreeData(
  repoId: string,
  data: TreeNodeData[],
  entityRefs: string[],
): Promise<void> {
  for (const entityRef of entityRefs) {
    const entityNode = findNode(data, entityRef);
    if (entityNode) {
      continue;
    }

    let lookedUpEntityRef = entityRef;
    let lookedUpEntitySiblingNodes: TreeNodeData[] = [];
    while (true) {
      const entitySiblings = await getLogEntitySiblings(
        repoId,
        lookedUpEntityRef,
      );
      const parentEntityRef = entitySiblings[0].parentEntityRef!;
      const entitySiblingNodes = entitySiblings.map(logEntityToTreeNodeData);
      const entityNode = findNode(entitySiblingNodes, lookedUpEntityRef)!;
      if (lookedUpEntitySiblingNodes.length > 0) {
        entityNode.children = lookedUpEntitySiblingNodes;
      }
      lookedUpEntitySiblingNodes = entitySiblingNodes;
      const parentNode = findNode(data, parentEntityRef);
      if (parentNode) {
        parentNode.children = lookedUpEntitySiblingNodes;
        break;
      } else {
        lookedUpEntityRef = parentEntityRef;
      }
    }
  }
}

function useLogEntityChildrenFetcher({
  repoId,
  tree,
  node,
  expanded,
}: {
  repoId: string;
  tree: UseTreeReturnType;
  node: TreeNodeData;
  expanded: boolean;
}): boolean {
  const query = useQuery({
    queryKey: ["logEntities", repoId, node.value],
    queryFn: () => getAllLogEntities(repoId!, node.value),
    enabled: expanded && node.children?.length === 0,
  });

  useEffect(() => {
    if (query.data) {
      node.children = query.data.map(logEntityToTreeNodeData);
      // force tree to re-render
      if (expanded) {
        tree.expand(node.value);
      }
    }
  }, [query.data]);

  return query.isLoading;
}

function useLogEntitiesTreeData(
  repoId: string,
  entityRefs: string[],
  onReset?: () => void,
) {
  const query = useQuery({
    queryKey: ["logEntities", repoId],
    queryFn: () => getAllLogEntities(repoId),
    enabled: !!repoId,
  });
  const [data, setData] = useState<TreeNodeData[]>([]);

  useEffect(() => {
    if (query.data) {
      setData(query.data.map(logEntityToTreeNodeData));
      // clear existing selected entities on new data/repo because they don't apply anymore
      if (onReset && data.length !== 0 && entityRefs.length !== 0) {
        onReset();
      }
    }
  }, [query.data]);

  useEffect(() => {
    if (
      data.length > 0 &&
      entityRefs.length > 0 &&
      entityRefs.some((entityRef) => !findNode(data, entityRef))
    ) {
      completeTreeData(repoId!, data, entityRefs).then(() =>
        setData((data) => data),
      );
    }
  }, [data, entityRefs]);

  return data;
}

function TreeNodeExpander({
  tree,
  node,
  expanded,
  loading,
}: {
  tree: UseTreeReturnType;
  node: TreeNodeData;
  expanded: boolean;
  loading: boolean;
}) {
  return node.children ? (
    <ActionIcon
      onClick={() =>
        expanded ? tree.collapse(node.value) : tree.expand(node.value)
      }
      variant="transparent"
      p="0"
      size="20px"
    >
      {expanded ? (
        loading ? (
          <Loader size={16} />
        ) : (
          <IconChevronDown style={iconSize(20)} />
        )
      ) : (
        <IconChevronRight style={iconSize(20)} />
      )}
    </ActionIcon>
  ) : (
    <Space w="20px" />
  );
}

function ScrollableTree({
  data,
  tree,
  renderNode,
  onClear,
}: {
  data: TreeNodeData[];
  tree: UseTreeReturnType;
  renderNode: (payload: RenderTreeNodePayload) => React.ReactNode;
  onClear: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Stack gap="0" p="0">
      <ScrollArea.Autosize type="hover" mah={200} p="8px" pr="0">
        <Box w="250px">
          <Tree
            data={data}
            tree={tree}
            levelOffset={18}
            expandOnClick={false}
            renderNode={renderNode}
          />
        </Box>
      </ScrollArea.Autosize>
      <Box
        style={{
          borderTopStyle: "solid",
          borderTopWidth: "1px",
          borderColor: "var(--mantine-color-gray-2)",
        }}
      >
        <Anchor onClick={onClear}>
          <Text size="xs" px="sm" py="6px">
            {t("common.clear")}
          </Text>
        </Anchor>
      </Box>
    </Stack>
  );
}

function TreeNode({
  repoId,
  selectedNodeValue,
  onChange,
  node,
  expanded,
  elementProps,
  tree,
}: {
  repoId: string;
  selectedNodeValue: string | null;
  onChange: (value: string) => void;
  node: TreeNodeData;
  expanded: boolean;
  elementProps: any;
  tree: UseTreeReturnType;
}) {
  const loading = useLogEntityChildrenFetcher({
    repoId,
    tree,
    node,
    expanded,
  });
  const checked = node.value === selectedNodeValue;
  const indeterminate =
    !checked &&
    selectedNodeValue &&
    hasAnyChildNodeChecked(node, [selectedNodeValue]);

  return (
    <Group {...elementProps}>
      <Group gap={0}>
        <TreeNodeExpander
          tree={tree}
          node={node}
          expanded={expanded}
          loading={loading}
        />
        <Button
          onClick={() => (!checked ? onChange(node.value) : onChange(""))}
          variant={checked ? "light" : "transparent"}
          size="sm"
          h="1.75rem"
          color={
            checked || indeterminate
              ? "var(--mantine-color-blue214-6)"
              : "black"
          }
          p="0.30rem"
          style={
            !checked && !indeterminate ? { fontWeight: "normal" } : undefined
          }
        >
          {node.label}
        </Button>
      </Group>
    </Group>
  );
}

function CheckTreeNode({
  repoId,
  entityRefs,
  onChange,
  node,
  expanded,
  elementProps,
  tree,
}: {
  repoId: string;
  entityRefs: string[];
  onChange: (value: string[]) => void;
  node: TreeNodeData;
  expanded: boolean;
  elementProps: any;
  tree: UseTreeReturnType;
}) {
  const loading = useLogEntityChildrenFetcher({
    repoId,
    tree,
    node,
    expanded,
  });
  const checked = entityRefs.includes(node.value);
  const indeterminate = !checked && hasAnyChildNodeChecked(node, entityRefs);

  const handleCheck = () => {
    if (!checked) {
      onChange([...entityRefs, node.value]);
    } else {
      onChange(entityRefs.filter((ref) => ref !== node.value));
    }
  };

  return (
    <Group {...elementProps} style={{ cursor: "default" }}>
      <Group gap="0px" p="4px">
        <TreeNodeExpander
          tree={tree}
          node={node}
          expanded={expanded}
          loading={loading}
        />
        <Space w="8px" />
        <Checkbox.Indicator
          checked={checked}
          indeterminate={indeterminate}
          onClick={handleCheck}
          size="xs"
        />
        <Space w="6px" />
        <Text onClick={handleCheck} size="sm" style={{ cursor: "default" }}>
          {node.label}
        </Text>
      </Group>
    </Group>
  );
}

export function EntitySelector({
  repoId,
  entityRef,
  onChange,
}: {
  repoId: string | null;
  entityRef: string;
  onChange: (value: string) => void;
}) {
  const entityRefs = useMemo(() => (entityRef ? [entityRef] : []), [entityRef]);
  const data = useLogEntitiesTreeData(repoId!, entityRefs, () => onChange(""));
  const tree = useTree({});

  return (
    <ScrollableTree
      data={data}
      tree={tree}
      renderNode={({ node, expanded, elementProps, tree }) => (
        <TreeNode
          repoId={repoId!}
          selectedNodeValue={entityRef}
          onChange={onChange}
          node={node}
          expanded={expanded}
          elementProps={elementProps}
          tree={tree}
        />
      )}
      onClear={() => entityRef !== "" && onChange("")}
    />
  );
}

interface MultiEntitySelectorProps {
  repoId: string;
  entityRefs: string[];
  onChange: (entityRefs: string[]) => void;
}

export function MultiEntitySelector({
  repoId,
  entityRefs,
  onChange,
}: MultiEntitySelectorProps) {
  const data = useLogEntitiesTreeData(repoId, entityRefs);
  const tree = useTree({});

  return (
    <ScrollableTree
      data={data}
      tree={tree}
      renderNode={({ node, expanded, elementProps, tree }) => (
        <CheckTreeNode
          repoId={repoId}
          entityRefs={entityRefs}
          onChange={onChange}
          node={node}
          expanded={expanded}
          elementProps={elementProps}
          tree={tree}
        />
      )}
      onClear={() => onChange([])}
    />
  );
}

interface MultiEntitySelectorPickerProps extends MultiEntitySelectorProps {
  disabled?: boolean;
}

export function MultiEntitySelectorPicker({
  repoId,
  entityRefs,
  onChange,
  disabled,
}: MultiEntitySelectorPickerProps) {
  const { t } = useTranslation();
  return (
    <PopoverForm
      title={t("permission.entities")}
      isFilled={entityRefs.length > 0}
      disabled={disabled}
    >
      <MultiEntitySelector
        repoId={repoId}
        entityRefs={entityRefs}
        onChange={onChange}
      />
    </PopoverForm>
  );
}
