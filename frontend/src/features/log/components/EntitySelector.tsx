import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { CheckTree, Tree } from "rsuite";
import "rsuite/dist/rsuite-no-reset.min.css";
import { ItemDataType } from "rsuite/esm/@types/common";

import { PopoverForm } from "@/components";

import { getAllLogEntities, getLogEntity, LogEntity } from "../api";

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

function logEntityToItem(entity: LogEntity): ItemDataType<string> {
  return {
    value: entity.ref,
    label: entity.name,
    children: entity.hasChildren ? [] : undefined,
  };
}

async function buildTreeBranch(
  repoId: string,
  entityRef: string,
  item: ItemDataType<string> | null,
  items: ItemDataType<string>[],
): Promise<[ItemDataType<string> | null, ItemDataType<string>[]]> {
  const entity = await getLogEntity(repoId, entityRef);
  // now we have the full entity, we can update the item label
  if (item) item.label = entity.name;

  // get all sibling entities
  const siblingEntities = await getAllLogEntities(
    repoId,
    entity.parentEntityRef || null,
  );
  const siblingItems = siblingEntities.map(logEntityToItem);

  if (item) {
    // restore the item with its children we got from the previous call
    for (let i = 0; i < siblingItems.length; i++) {
      if (siblingItems[i].value === entityRef) {
        siblingItems[i] = item;
        break;
      }
    }
  }

  if (entity.parentEntityRef === null) {
    // no more parent, we just fetch the top entities (the entity selector has not been opened yet probably)
    return [null, siblingItems];
  } else {
    const parentItem = lookupItem(entity.parentEntityRef, items);
    if (parentItem) {
      // we reached an already fetched parent entity in the tree, return it alongside its children
      return [parentItem, siblingItems];
    } else {
      // we need to fetch the parent entity and its children
      const parentItem = {
        value: entity.parentEntityRef,
        children: siblingItems,
      };
      return buildTreeBranch(repoId, entity.parentEntityRef, parentItem, items);
    }
  }
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
  const [items, setItems] = useState<ItemDataType<string>[]>([]);
  const currentEntityRef = useRef<string>("");
  const queryClient = useQueryClient();

  // load top-level entities
  useEffect(() => {
    if (repoId) {
      queryClient
        .ensureQueryData({
          queryKey: ["logConsolidatedData", "entity", repoId],
          queryFn: () => getAllLogEntities(repoId),
        })
        .then((entities) => setItems(entities.map(logEntityToItem)));
    }
  }, [repoId]);

  // load the tree branch of the selected entity
  useEffect(() => {
    let enabled = true;

    if (!entityRef || lookupItem(entityRef, items)) {
      return;
    }

    buildTreeBranch(repoId!, entityRef, null, items).then(
      ([parentItem, childrenItems]) => {
        if (!enabled) {
          return;
        }

        if (!parentItem) {
          setItems(childrenItems);
        } else {
          parentItem.children = childrenItems;
          setItems([...items]);
        }
      },
    );

    return () => {
      enabled = false;
    };
  }, [entityRef]);

  return (
    <Tree
      data={items}
      value={entityRef || ""}
      onSelect={(item) => {
        // implement an unselect behavior, which is not supported by the Tree component
        if (item.value === currentEntityRef.current) {
          currentEntityRef.current = "";
          onChange("");
        } else {
          currentEntityRef.current = item.value as string;
          onChange(item.value as string);
        }
      }}
      getChildren={async (item) => {
        // NB: beware that items are changed under the hood without using setItems by the Tree component
        // after getChildren has been called
        return queryClient
          .ensureQueryData({
            queryKey: ["logConsolidatedData", "entity", repoId, item.value],
            queryFn: () => getAllLogEntities(repoId!, item.value as string),
          })
          .then((entities) => {
            return entities.map(logEntityToItem);
          });
      }}
      searchable={false}
      style={{ width: 200, height: 250 }}
    />
  );
}

interface MultiEntitySelectorProps {
  repoId: string;
  entityRefs: string[];
  onChange: (value: string[]) => void;
}

// FIXME: this component shares a lot of code with EntitySelector, we should refactor it
export function MultiEntitySelector({
  repoId,
  entityRefs,
  onChange,
}: MultiEntitySelectorProps) {
  const [items, setItems] = useState<ItemDataType<string>[]>([]);
  const queryClient = useQueryClient();

  // load top-level entities
  useEffect(() => {
    queryClient
      .ensureQueryData({
        queryKey: ["logConsolidatedData", "entity", repoId],
        queryFn: () => getAllLogEntities(repoId),
      })
      .then((entities) => setItems(entities.map(logEntityToItem)));
  }, []);

  // load the tree branch of the selected entity
  useEffect(() => {
    let enabled = true;

    for (const entityRef of entityRefs) {
      if (lookupItem(entityRef, items)) {
        continue;
      }

      buildTreeBranch(repoId, entityRef, null, items).then(
        ([parentItem, childrenItems]) => {
          if (!enabled) {
            return;
          }

          if (!parentItem) {
            setItems(childrenItems);
          } else {
            parentItem.children = childrenItems;
            setItems([...items]);
          }
        },
      );
    }

    return () => {
      enabled = false;
    };
  }, [entityRefs]);

  return (
    <CheckTree
      data={items}
      value={entityRefs}
      onChange={(value) => onChange(value as string[])}
      getChildren={async (item) => {
        // NB: beware that items are changed under the hood without using setItems by the Tree component
        // after getChildren has been called
        return queryClient
          .ensureQueryData({
            queryKey: ["logConsolidatedData", "entity", repoId, item.value],
            queryFn: () => getAllLogEntities(repoId!, item.value as string),
          })
          .then((entities) => {
            return entities.map(logEntityToItem);
          });
      }}
      cascade={false}
      searchable={false}
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
  return (
    <PopoverForm
      title="Entities"
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
