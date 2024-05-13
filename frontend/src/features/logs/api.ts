import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { getAllPagePaginatedItems, reqGet } from "@/utils/api";
import { serializeDate } from "@/utils/date";

dayjs.extend(utc);

export type Log = {
  id: number;
  savedAt: string;
  event: {
    name: string;
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
    id: string;
    name: string;
  }[];
};

export type LogNode = {
  id: string;
  name: string;
  parentNodeId: string | null;
  hasChildren: boolean;
};

export type LogsFilterParams = {
  repoId?: string;
  eventCategory?: string;
  eventName?: string;
  actorType?: string;
  actorName?: string;
  resourceType?: string;
  resourceName?: string;
  tagCategory?: string;
  tagName?: string;
  tagId?: string;
  nodeId?: string;
  since?: Date | null;
  until?: Date | null;
};

export function buildEmptyLogsFilterParams(): LogsFilterParams {
  return {
    repoId: "",
    eventCategory: "",
    eventName: "",
    actorType: "",
    actorName: "",
    resourceType: "",
    resourceName: "",
    tagCategory: "",
    tagName: "",
    tagId: "",
    nodeId: "",
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
    eventCategory: filter?.eventCategory,
    eventName: filter?.eventName,
    actorType: filter?.actorType,
    actorName: filter?.actorName,
    resourceType: filter?.resourceType,
    resourceName: filter?.resourceName,
    tagCategory: filter?.tagCategory,
    tagName: filter?.tagName,
    tagId: filter?.tagId,
    nodeId: filter?.nodeId,
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

export async function getAllLogEventCategories(
  repoId: string,
): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/event-categories`,
    {},
  );
}

export async function getAllLogEventNames(
  repoId: string,
  category?: string,
): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/events`,
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
  parentNodeId?: string | null,
): Promise<LogNode[]> {
  return getAllPagePaginatedItems<LogNode>(
    `/repos/${repoId}/logs/nodes`,
    parentNodeId ? { parentNodeId: parentNodeId } : { root: true },
  );
}

export async function getLogNode(
  repoId: string,
  nodeId: string,
): Promise<LogNode> {
  return await reqGet(`/repos/${repoId}/logs/nodes/${nodeId}`);
}
