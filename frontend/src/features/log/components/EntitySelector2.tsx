import {
  ActionIcon,
  Box,
  Button,
  Group,
  Loader,
  RenderTreeNodePayload,
  ScrollArea,
  Space,
  Tree,
  TreeNodeData,
  useTree,
  UseTreeReturnType,
} from "@mantine/core";
import { IconChevronDown, IconChevronRight } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

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

async function getLogEntitySiblings(
  repoId: string,
  entityRef: string,
): Promise<LogEntity[]> {
  const entity = await getLogEntity(repoId, entityRef);
  return getAllLogEntities(repoId, entity.parentEntityRef);
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

function hasAnyChildNodeChecked(node: TreeNodeData, checkedNode: string) {
  if (node.value === checkedNode) {
    return true;
  }
  if (node.children) {
    for (const child of node.children) {
      if (hasAnyChildNodeChecked(child, checkedNode)) {
        return true;
      }
    }
  }
  return false;
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
  const query = useQuery({
    queryKey: ["logConsolidatedData", "entity", repoId, node.value],
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

  const checked = node.value === selectedNodeValue;
  const indeterminate =
    !checked && hasAnyChildNodeChecked(node, selectedNodeValue!);

  return (
    <Group {...elementProps}>
      <Group gap={0}>
        {node.children ? (
          <ActionIcon
            onClick={() =>
              expanded ? tree.collapse(node.value) : tree.expand(node.value)
            }
            variant="transparent"
            p="0px"
            size="20"
          >
            {expanded ? (
              query.isLoading ? (
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
        )}
        <Button
          onClick={() => (!checked ? onChange(node.value) : onChange(""))}
          variant={checked ? "light" : "transparent"}
          size="sm"
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

function makeTreeNodeRenderer(
  repoId: string,
  entityRef: string | null,
  onChange: (value: string) => void,
) {
  function renderTreeNode({
    node,
    expanded,
    elementProps,
    tree,
  }: RenderTreeNodePayload) {
    return (
      <TreeNode
        repoId={repoId}
        selectedNodeValue={entityRef}
        onChange={onChange}
        node={node}
        expanded={expanded}
        elementProps={elementProps}
        tree={tree}
      />
    );
  }

  return renderTreeNode;
}

function logEntityToTreeNodeData(entity: LogEntity): TreeNodeData {
  return {
    value: entity.ref,
    label: entity.name,
    // An empty array means that the node has children, but they have not been loaded yet
    children: entity.hasChildren ? [] : undefined,
  };
}

export function EntitySelector({
  repoId,
  entityRef,
  onChange,
}: {
  repoId: string | null;
  entityRef: string | null;
  onChange: (value: string) => void;
}) {
  const query = useQuery({
    queryKey: ["logEntities", repoId],
    queryFn: () => getAllLogEntities(repoId!),
    enabled: !!repoId,
  });
  const [data, setData] = useState<TreeNodeData[]>([]);
  const tree = useTree({});

  useEffect(() => {
    if (!query.data) {
      return;
    }
    if (data.length === 0) {
      setData(query.data.map(logEntityToTreeNodeData));
    } else if (entityRef && !findNode(data, entityRef)) {
      completeTreeData(repoId!, data, [entityRef]).then(() =>
        setData((data) => data),
      );
    }
  }, [query.data, data, entityRef]);

  return (
    <ScrollArea.Autosize type="hover" mah={200}>
      <Box px="8px" py="6px" w="250px">
        <Tree
          data={data}
          tree={tree}
          levelOffset={18}
          expandOnClick={false}
          renderNode={makeTreeNodeRenderer(repoId!, entityRef, onChange)}
        />
      </Box>
    </ScrollArea.Autosize>
  );
}
