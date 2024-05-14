import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { getAllPagePaginatedItems, reqGet } from "@/utils/api";
import { serializeDate } from "@/utils/date";

dayjs.extend(utc);

export type Named = {
  name: string;
};

export type Log = {
  id: number;
  savedAt: string;
  action: {
    type: string;
    category: string;
  };
  actor?: {
    type: string;
    id: string;
    name: string;
  };
  resource?: {
    type: string;
    id: string;
    name: string;
  };
  nodePath: {
    ref: string;
    name: string;
  }[];
};

export type LogNode = {
  ref: string;
  name: string;
  parentNodeRef: string | null;
  hasChildren: boolean;
};

export type LogsFilterParams = {
  repoId?: string;
  actionCategory?: string;
  actionType?: string;
  actorType?: string;
  actorName?: string;
  resourceType?: string;
  resourceName?: string;
  tagCategory?: string;
  tagName?: string;
  tagId?: string;
  nodeRef?: string;
  since?: Date | null;
  until?: Date | null;
};

export function buildEmptyLogsFilterParams(): LogsFilterParams {
  return {
    repoId: "",
    actionCategory: "",
    actionType: "",
    actorType: "",
    actorName: "",
    resourceType: "",
    resourceName: "",
    tagCategory: "",
    tagName: "",
    tagId: "",
    nodeRef: "",
    since: null,
    until: null,
  };
}

export async function getLogs(
  cursor: string | null,
  filter?: LogsFilterParams,
  limit = 3,
): Promise<{ logs: Log[]; nextCursor: string | null }> {
  const data = await reqGet(`/repos/${filter!.repoId}/logs`, {
    limit,
    since: filter?.since ? serializeDate(filter.since) : undefined,
    until: filter?.until ? serializeDate(filter.until) : undefined,
    actionCategory: filter?.actionCategory,
    actionType: filter?.actionType,
    actorType: filter?.actorType,
    actorName: filter?.actorName,
    resourceType: filter?.resourceType,
    resourceName: filter?.resourceName,
    tagCategory: filter?.tagCategory,
    tagName: filter?.tagName,
    tagId: filter?.tagId,
    nodeRef: filter?.nodeRef,
    ...(cursor && { cursor }),
  });
  return {
    logs: data.data,
    nextCursor: data.pagination.nextCursor,
  };
}

export async function getLog(repoId: string, logId: string): Promise<Log> {
  return await reqGet(`/repos/${repoId}/logs/${logId}`);
}

export async function getAllLogActionCategories(
  repoId: string,
): Promise<Named[]> {
  return getAllPagePaginatedItems<Named>(
    `/repos/${repoId}/logs/actions/categories`,
    {},
  );
}

export async function getAllLogActionTypes(
  repoId: string,
  category?: string,
): Promise<Named[]> {
  return getAllPagePaginatedItems<Named>(
    `/repos/${repoId}/logs/actions/types`,
    category ? { category } : {},
  );
}

export async function getAllLogActorTypes(repoId: string): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/actor-types`,
    {},
  );
}

export async function getAllLogResourceTypes(
  repoId: string,
): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/resource-types`,
    {},
  );
}

export async function getAllLogTagCategories(
  repoId: string,
): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/tag-categories`,
    {},
  );
}

export async function getAllLogNodes(
  repoId: string,
  parentNodeRef?: string | null,
): Promise<LogNode[]> {
  return getAllPagePaginatedItems<LogNode>(
    `/repos/${repoId}/logs/nodes`,
    parentNodeRef ? { parentNodeRef: parentNodeRef } : { root: true },
  );
}

export async function getLogNode(
  repoId: string,
  nodeRef: string,
): Promise<LogNode> {
  return await reqGet(`/repos/${repoId}/logs/nodes/ref:${nodeRef}`);
}
