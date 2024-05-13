import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Tree } from "rsuite";
import "rsuite/dist/rsuite-no-reset.min.css";
import { ItemDataType } from "rsuite/esm/@types/common";

import { getAllLogNodes, getLogNode, LogNode } from "../api";

function lookupItem(
  itemValue: string,
  items: ItemDataType<string>[],
): ItemDataType<string> | null {
  for (const item of items) {
    if (item.value === itemValue) return item;
    if (item.children) {
      const found = lookupItem(itemValue, item.children);
      if (found) return found;
    }
  }
  return null;
}

function logNodeToItem(node: LogNode): ItemDataType<string> {
  return {
    value: node.ref,
    label: node.name,
    children: node.hasChildren ? [] : undefined,
  };
}

async function buildTreeBranch(
  repoId: string,
  nodeRef: string,
  item: ItemDataType<string> | null,
  items: ItemDataType<string>[],
): Promise<[ItemDataType<string> | null, ItemDataType<string>[]]> {
  const node = await getLogNode(repoId, nodeRef);
  // now we have the full node, we can update the item label
  if (item) item.label = node.name;

  // get all sibling nodes
  const siblingNodes = await getAllLogNodes(repoId, node.parentNodeRef || null);
  const siblingItems = siblingNodes.map(logNodeToItem);

  if (item) {
    // restore the item with its children we got from the previous call
    for (let i = 0; i < siblingItems.length; i++) {
      if (siblingItems[i].value === nodeRef) {
        siblingItems[i] = item;
        break;
      }
    }
  }

  if (node.parentNodeRef === null) {
    // no more parent, we just fetch the top nodes (the node selector has not been opened yet probably)
    return [null, siblingItems];
  } else {
    const parentItem = lookupItem(node.parentNodeRef, items);
    if (parentItem) {
      // we reached an already fetched parent node in the tree, return it alongside its children
      return [parentItem, siblingItems];
    } else {
      // we need to fetch the parent node and its children
      const parentItem = {
        value: node.parentNodeRef,
        children: siblingItems,
      };
      return buildTreeBranch(repoId, node.parentNodeRef, parentItem, items);
    }
  }
}

export function NodeSelector({
  repoId,
  nodeRef,
  onChange,
}: {
  repoId: string | null;
  nodeRef: string | null;
  onChange: (value: string) => void;
}) {
  const [items, setItems] = useState<ItemDataType<string>[]>([]);
  const currentNodeRef = useRef<string>("");
  const queryClient = useQueryClient();

  // load top-level nodes
  useEffect(() => {
    if (repoId) {
      queryClient
        .ensureQueryData({
          queryKey: ["nodes", repoId],
          queryFn: () => getAllLogNodes(repoId),
        })
        .then((nodes) => setItems(nodes.map(logNodeToItem)));
    }
  }, [repoId]);

  // load the tree branch of the selected node
  useEffect(() => {
    let enabled = true;

    if (!nodeRef || lookupItem(nodeRef, items)) return;

    buildTreeBranch(repoId!, nodeRef, null, items).then(
      ([parentItem, childrenItems]) => {
        if (!enabled) return;

        if (!parentItem) {
          setItems(childrenItems);
        } else {
          parentItem.children = childrenItems;
          setItems([...items]);
        }

        return () => {
          enabled = false;
        };
      },
    );
  }, [nodeRef]);

  return (
    <Tree
      data={items}
      value={nodeRef || ""}
      onSelect={(item) => {
        // implement an unselect behavior, which is not supported by the Tree component
        if (item.value === currentNodeRef.current) {
          currentNodeRef.current = "";
          onChange("");
        } else {
          currentNodeRef.current = item.value as string;
          onChange(item.value as string);
        }
      }}
      getChildren={async (item) => {
        // NB: beware that items are changed under the hood without using setItems by the Tree component
        // after getChildren has been called
        return queryClient
          .ensureQueryData({
            queryKey: ["nodes", repoId, item.value],
            queryFn: () => getAllLogNodes(repoId!, item.value as string),
          })
          .then((nodes) => {
            return nodes.map(logNodeToItem);
          });
      }}
      searchable={false}
      style={{ width: 200, height: 250 }}
    />
  );
}
