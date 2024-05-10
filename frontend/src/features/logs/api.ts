import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { getAllPagePaginatedItems } from "@/utils/api";
import { axiosInstance } from "@/utils/axios";
import { serializeDate } from "@/utils/date";

dayjs.extend(utc);

export type Log = {
  id: number;
  saved_at: string;
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
  node_path: {
    id: string;
    name: string;
  }[];
};

export type LogNode = {
  id: string;
  name: string;
  parent_node_id: string | null;
  has_children: boolean;
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
  const response = await axiosInstance.get(`/repos/${filter!.repoId}/logs`, {
    params: {
      limit,
      since: filter?.since ? serializeDate(filter.since) : undefined,
      until: filter?.until ? serializeDate(filter.until) : undefined,
      event_category: filter?.eventCategory,
      event_name: filter?.eventName,
      actor_type: filter?.actorType,
      actor_name: filter?.actorName,
      resource_type: filter?.resourceType,
      resource_name: filter?.resourceName,
      tag_category: filter?.tagCategory,
      tag_name: filter?.tagName,
      tag_id: filter?.tagId,
      node_id: filter?.nodeId,
      ...(cursor && { cursor }),
    },
  });
  return {
    logs: response.data.data,
    nextCursor: response.data.pagination.next_cursor,
  };
}

export async function getLog(repoId: string, logId: string): Promise<Log> {
  return (await axiosInstance.get(`/repos/${repoId}/logs/${logId}`)).data;
}

export async function getAllLogEventCategories(
  repoId: string,
): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/event-categories`,
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
  return getAllPagePaginatedItems<string>(`/repos/${repoId}/logs/actor-types`);
}

export async function getAllLogResourceTypes(
  repoId: string,
): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/resource-types`,
  );
}

export async function getAllLogTagCategories(
  repoId: string,
): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `/repos/${repoId}/logs/tag-categories`,
  );
}

export async function getAllLogNodes(
  repoId: string,
  parent_node_id?: string | null,
): Promise<LogNode[]> {
  return getAllPagePaginatedItems<LogNode>(
    `/repos/${repoId}/logs/nodes`,
    parent_node_id ? { parent_node_id } : { root: true },
  );
}

export async function getLogNode(
  repoId: string,
  nodeId: string,
): Promise<LogNode> {
  return (await axiosInstance.get(`/repos/${repoId}/logs/nodes/${nodeId}`))
    .data;
}
