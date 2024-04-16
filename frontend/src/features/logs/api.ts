import { getAllPagePaginatedItems } from '@/utils/api';
import { timeout } from '@/utils/api';
import axios from 'axios';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
dayjs.extend(utc);

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
}

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
    until: null
  };
}

function formatDate(date: Date) {
  return dayjs(date).utc().format("YYYY-MM-DDTHH:mm:ss") + "Z";
}

export async function getLogs(cursor: string | null, filter?: LogsFilterParams, limit = 3): Promise<{logs: Log[], nextCursor: string | null}> {
  await timeout(300);  // FIXME: Simulate network latency

  const response = await axios.get(`http://localhost:8000/repos/${filter!.repoId}/logs`, {
    params: {
      limit,
      since: filter?.since ? formatDate(filter.since) : undefined,
      until: filter?.until ? formatDate(filter.until) : undefined,
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
      ...(cursor && { cursor })
    }
  });
  return {logs: response.data.data, nextCursor: response.data.pagination.next_cursor};
}

export async function getAllLogEventCategories(repoId: string): Promise<string[]> {
  return getAllPagePaginatedItems<string>(`http://localhost:8000/repos/${repoId}/logs/event-categories`);
}

export async function getAllLogEventNames(repoId: string, category?: string): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    `http://localhost:8000/repos/${repoId}/logs/events`, category ? {category} : {}
  );
}

export async function getAllLogActorTypes(repoId: string): Promise<string[]> {
  return getAllPagePaginatedItems<string>(`http://localhost:8000/repos/${repoId}/logs/actor-types`);
}

export async function getAllLogResourceTypes(repoId: string): Promise<string[]> {
  return getAllPagePaginatedItems<string>(`http://localhost:8000/repos/${repoId}/logs/resource-types`);
}

export async function getAllLogTagCategories(repoId: string): Promise<string[]> {
  return getAllPagePaginatedItems<string>(`http://localhost:8000/repos/${repoId}/logs/tag-categories`);
}

export async function getAllLogNodes(repoId: string, parent_node_id?: string | null): Promise<LogNode[]> {
  return getAllPagePaginatedItems<LogNode>(
    `http://localhost:8000/repos/${repoId}/logs/nodes`,
    parent_node_id ? {parent_node_id} : {root: true}
  );
}

export async function getLogNode(repoId: string, nodeId: string): Promise<LogNode> {
  return (await axios.get(`http://localhost:8000/repos/${repoId}/logs/nodes/${nodeId}`)).data;
}
