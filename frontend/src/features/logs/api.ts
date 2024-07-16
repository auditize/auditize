import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import snakecaseKeys from "snakecase-keys";

import { getAllPagePaginatedItems, reqGet } from "@/utils/api";
import { serializeDate } from "@/utils/date";

dayjs.extend(utc);

export type Named = {
  name: string;
};

export type CustomField = {
  name: string;
  value: string;
};

type Tag = {
  ref: string | null;
  type: string;
  name: string | null;
};

type Attachment = {
  name: string;
  description: string;
  type: string;
  mimeType: string;
};

export type Log = {
  id: string;
  savedAt: string;
  action: {
    type: string;
    category: string;
  };
  source: CustomField[];
  actor?: {
    ref: string;
    type: string;
    name: string;
    extra: CustomField[];
  };
  resource?: {
    ref: string;
    type: string;
    name: string;
    extra: CustomField[];
  };
  details: CustomField[];
  nodePath: {
    ref: string;
    name: string;
  }[];
  tags: Tag[];
  attachments: Attachment[];
};

export type LogNode = {
  ref: string;
  name: string;
  parentNodeRef: string | null;
  hasChildren: boolean;
};

export type LogSearchParams = {
  repoId: string;
  actionCategory: string;
  actionType: string;
  actorType: string;
  actorName: string;
  actorRef: string;
  actorExtra: Map<string, string>;
  source: Map<string, string>;
  resourceType: string;
  resourceName: string;
  resourceRef: string;
  resourceExtra: Map<string, string>;
  details: Map<string, string>;
  tagRef: string;
  tagType: string;
  tagName: string;
  attachmentName: string;
  attachmentDescription: string;
  attachmentType: string;
  attachmentMimeType: string;
  nodeRef: string;
  since: Date | null;
  until: Date | null;
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
    attachmentName: "",
    attachmentDescription: "",
    attachmentType: "",
    attachmentMimeType: "",
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
      `${prefix}.${name}`,
      value,
    ]),
  );
}

export function prepareLogSearchParamsForApi(
  params: LogSearchParams,
  { includeRepoId } = { includeRepoId: true },
): object {
  const prepared = {
    ...(includeRepoId ? { repoId: params.repoId } : {}),

    // Dates
    since: params.since ? serializeDate(params.since) : undefined,
    until: params.until ? serializeDate(params.until) : undefined,

    // Action
    actionCategory: params.actionCategory,
    actionType: params.actionType,

    // Actor
    actorType: params.actorType,
    actorName: params.actorName,
    actorRef: params.actorRef,
    ...prepareCustomFieldsForApi(params.actorExtra, "actor"),

    // Source
    ...prepareCustomFieldsForApi(params.source, "source"),

    // Resource
    resourceType: params.resourceType,
    resourceName: params.resourceName,
    resourceRef: params.resourceRef,
    ...prepareCustomFieldsForApi(params.resourceExtra, "resource"),

    // Details
    ...prepareCustomFieldsForApi(params.details, "details"),

    // Tag
    tagRef: params.tagRef,
    tagType: params.tagType,
    tagName: params.tagName,

    // Attachment
    attachmentName: params.attachmentName,
    attachmentDescription: params.attachmentDescription,
    attachmentType: params.attachmentType,
    attachmentMimeType: params.attachmentMimeType,

    // Node
    nodeRef: params.nodeRef,
  };

  return Object.fromEntries(
    Object.entries(prepared).filter(([, value]) => value),
  );
}

function stripEmptyStringsFromObject(obj: any): any {
  // Make the query string prettier by avoid query keys without values
  return Object.fromEntries(
    Object.entries(obj).filter(([_, value]) => (value !== "" && value !== undefined)), // prettier-ignore
  );
}

export function logSearchParamsToURLSearchParams(
  params: LogSearchParams,
  {
    includeRepoId = true,
    snakecase = false,
  }: {
    includeRepoId?: boolean;
    snakecase?: boolean;
  } = {},
): URLSearchParams {
  let prepared = stripEmptyStringsFromObject(
    prepareLogSearchParamsForApi(params, { includeRepoId }),
  );
  if (snakecase) {
    prepared = snakecaseKeys(prepared, { exclude: [/.*\..*/] }); // exclude custom fields (i.e "actor.role"));
  }
  return new URLSearchParams(prepared);
}

export async function getLogs(
  cursor: string | null,
  params?: LogSearchParams,
  limit = 30,
): Promise<{ logs: Log[]; nextCursor: string | null }> {
  const data = await reqGet(
    `/repos/${params!.repoId}/logs`,
    snakecaseKeys(
      {
        limit,
        ...(params
          ? prepareLogSearchParamsForApi(params, { includeRepoId: false })
          : {}),
        ...(cursor && { cursor }),
      },
      { exclude: [/.*\..*/] }, // exclude custom fields (i.e "actor.role")
    ),
    { disableParamsSnakecase: true },
  );
  return {
    logs: data.items,
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

export async function getAllAttachmentTypes(repoId: string): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(
      `/repos/${repoId}/logs/attachments/types`,
      {},
    ),
  );
}

export async function getAllAttachmentMimeTypes(
  repoId: string,
): Promise<string[]> {
  return getNames(
    getAllPagePaginatedItems<Named>(
      `/repos/${repoId}/logs/attachments/mime-types`,
      {},
    ),
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
