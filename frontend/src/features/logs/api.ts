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

  const response = await axios.get('http://localhost:8000/logs', {
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

export async function getAllLogEventCategories(): Promise<string[]> {
  return getAllPagePaginatedItems<string>('http://localhost:8000/logs/event-categories');
}

export async function getAllLogEventNames(category?: string): Promise<string[]> {
  return getAllPagePaginatedItems<string>(
    'http://localhost:8000/logs/events', category ? {category} : {}
  );
}

export async function getAllLogActorTypes(): Promise<string[]> {
  return getAllPagePaginatedItems<string>('http://localhost:8000/logs/actor-types');
}

export async function getAllLogResourceTypes(): Promise<string[]> {
  return getAllPagePaginatedItems<string>('http://localhost:8000/logs/resource-types');
}

export async function getAllLogTagCategories(): Promise<string[]> {
  return getAllPagePaginatedItems<string>('http://localhost:8000/logs/tag-categories');
}

export async function getAllLogNodes(parent_node_id?: string | null): Promise<LogNode[]> {
  return getAllPagePaginatedItems<LogNode>(
    'http://localhost:8000/logs/nodes',
    parent_node_id ? {parent_node_id} : {root: true}
  );
}

export async function getLogNode(node_id: string): Promise<LogNode> {
  return (await axios.get(`http://localhost:8000/logs/nodes/${node_id}`)).data;
}
