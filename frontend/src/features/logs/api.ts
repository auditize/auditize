import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import snakecaseKeys from "snakecase-keys";

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
    ref: string;
    type: string;
    name: string;
  };
  resource?: {
    ref: string;
    type: string;
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

export type LogSearchParams = {
  repoId?: string;
  actionCategory?: string;
  actionType?: string;
  actorType?: string;
  actorName?: string;
  actorRef?: string;
  actorExtra?: Map<string, string>;
  source?: Map<string, string>;
  resourceType?: string;
  resourceName?: string;
  resourceRef?: string;
  resourceExtra?: Map<string, string>;
  details?: Map<string, string>;
  tagRef?: string;
  tagType?: string;
  tagName?: string;
  nodeRef?: string;
  since?: Date | null;
  until?: Date | null;
};

export function buildLogSearchParams(): LogSearchParams {
  return {
    repoId: "",
    actionCategory: "",
    actionType: "",
    actorType: "",
    actorName: "",
    actorRef: "",
    actorExtra: new Map(),
    source: new Map(),
    resourceType: "",
    resourceName: "",
    resourceRef: "",
    resourceExtra: new Map(),
    details: new Map(),
    tagType: "",
    tagName: "",
    tagRef: "",
    nodeRef: "",
    since: null,
    until: null,
  };
}

function prepareCustomFieldsForApi(
  fields: Map<string, string>,
  prefix: string,
): object {
  return Object.fromEntries(
    Array.from(fields.entries()).map(([name, value]) => [
      `${prefix}[${name}]`,
      value,
    ]),
  );
}

export function prepareLogFilterForApi(filter: LogSearchParams): object {
  return {
    repoId: filter.repoId,

    // Dates
    since: filter.since ? serializeDate(filter.since) : undefined,
    until: filter.until ? serializeDate(filter.until) : undefined,

    // Action
    actionCategory: filter.actionCategory,
    actionType: filter.actionType,

    // Actor
    actorType: filter.actorType,
    actorName: filter.actorName,
    actorRef: filter.actorRef,
    ...(filter.actorExtra &&
      prepareCustomFieldsForApi(filter.actorExtra, "actor")),

    // Source
    ...(filter.source && prepareCustomFieldsForApi(filter.source, "source")),

    // Resource
    resourceType: filter.resourceType,
    resourceName: filter.resourceName,
    resourceRef: filter.resourceRef,
    ...(filter.resourceExtra &&
      prepareCustomFieldsForApi(filter.resourceExtra, "resource")),

    // Details
    ...(filter.details && prepareCustomFieldsForApi(filter.details, "details")),

    // Tag
    tagRef: filter.tagRef,
    tagType: filter.tagType,
    tagName: filter.tagName,

    // Node
    nodeRef: filter.nodeRef,
  };
}

export async function getLogs(
  cursor: string | null,
  filter?: LogSearchParams,
  limit = 3,
): Promise<{ logs: Log[]; nextCursor: string | null }> {
  const data = await reqGet(
    `/repos/${filter!.repoId}/logs`,
    snakecaseKeys(
      {
        limit,
        ...(filter ? prepareLogFilterForApi(filter) : {}),
        repoId: undefined, // remove repoId from the query params
        ...(cursor && { cursor }),
      },
      { exclude: [/.*\[.*/] },
    ),
    { disableParamsSnakecase: true },
  );
  return {
    logs: data.data,
    nextCursor: data.pagination.nextCursor,
  };
}

export async function getLog(repoId: string, logId: string): Promise<Log> {
  return await reqGet(`/repos/${repoId}/logs/${logId}`);
}

async function getNames(promise: Promise<Named[]>): Promise<string[]> {
  return promise.then((named) => named.map((n) => n.name));
}

export async function getAllLogActionCategories(
  repoId: string,
): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(
      `/repos/${repoId}/logs/actions/categories`,
      {},
    ),
  );
}

export async function getAllLogActionTypes(
  repoId: string,
  category?: string,
): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(
      `/repos/${repoId}/logs/actions/types`,
      category ? { category } : {},
    ),
  );
}

export async function getAllLogActorTypes(repoId: string): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(`/repos/${repoId}/logs/actors/types`, {}),
  );
}

export async function getAllLogActorCustomFields(
  repoId: string,
): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(`/repos/${repoId}/logs/actors/extras`, {}),
  );
}

export async function getAllLogSourceFields(repoId: string): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(`/repos/${repoId}/logs/sources`, {}),
  );
}

export async function getAllLogResourceTypes(
  repoId: string,
): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(
      `/repos/${repoId}/logs/resources/types`,
      {},
    ),
  );
}

export async function getAllLogResourceCustomFields(
  repoId: string,
): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(
      `/repos/${repoId}/logs/resources/extras`,
      {},
    ),
  );
}

export async function getAllLogDetailFields(repoId: string): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(`/repos/${repoId}/logs/details`, {}),
  );
}

export async function getAllLogTagTypes(repoId: string): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(`/repos/${repoId}/logs/tags/types`, {}),
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
