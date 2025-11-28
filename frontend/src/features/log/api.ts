import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { getAllCursorPaginatedItems, reqGet } from "@/utils/api";

import { LogSearchParams } from "./LogSearchParams";

dayjs.extend(utc);

export type Name = {
  name: string;
};

export type Value = {
  value: string;
};

export type NameRefPair = {
  name: string;
  ref: string;
};

export enum CustomFieldType {
  String = "string",
  Enum = "enum",
  Boolean = "boolean",
  Json = "json",
  Integer = "integer",
  Float = "float",
}

export type CustomField = {
  name: string;
  value: string;
  type: CustomFieldType;
};

export type AvailableCustomField = {
  name: string;
  type: CustomFieldType;
};

type Tag = {
  ref: string | null;
  type: string;
  name: string | null;
};

type Attachment = {
  name: string;
  type: string;
  mimeType: string;
};

export type Actor = {
  ref: string;
  type: string;
  name: string;
  extra: CustomField[];
};

export type Resource = {
  ref: string;
  type: string;
  name: string;
  extra: CustomField[];
};

export type Log = {
  id: string;
  savedAt: string;
  action: {
    type: string;
    category: string;
  };
  source: CustomField[];
  actor?: Actor;
  resource?: Resource;
  details: CustomField[];
  entityPath: {
    ref: string;
    name: string;
  }[];
  tags: Tag[];
  attachments: Attachment[];
};

export type LogEntity = {
  ref: string;
  name: string;
  parentEntityRef: string | null;
  hasChildren: boolean;
};

export async function getLogs(
  cursor: string | null,
  params: LogSearchParams,
  limit = 30,
): Promise<{ logs: Log[]; nextCursor: string | null }> {
  const data = await reqGet(`/repos/${params.repoId}/logs`, {
    limit,
    ...params.serialize({ includeRepoId: false }),
    ...(cursor && { cursor }),
  });
  return {
    logs: data.items,
    nextCursor: data.pagination.nextCursor,
  };
}

export async function getLog(repoId: string, logId: string): Promise<Log> {
  return await reqGet(`/repos/${repoId}/logs/${logId}`);
}

async function getNames(promise: Promise<Name[]>): Promise<string[]> {
  return promise.then((names) => names.map((n) => n.name));
}

export async function getAllActionCategories(
  repoId: string,
): Promise<string[]> {
  return getNames(
    getAllCursorPaginatedItems<Name>(
      `/repos/${repoId}/logs/aggs/actions/categories`,
      {},
    ),
  );
}

export async function getAllActionTypes(
  repoId: string,
  category?: string,
): Promise<string[]> {
  return getNames(
    getAllCursorPaginatedItems<Name>(
      `/repos/${repoId}/logs/aggs/actions/types`,
      category ? { category } : {},
    ),
  );
}

export async function getAllActorTypes(repoId: string): Promise<string[]> {
  return getNames(
    getAllCursorPaginatedItems<Name>(
      `/repos/${repoId}/logs/aggs/actors/types`,
      {},
    ),
  );
}

export async function getAllActorCustomFields(
  repoId: string,
): Promise<AvailableCustomField[]> {
  return await getAllCursorPaginatedItems<AvailableCustomField>(
    `/repos/${repoId}/logs/actors/extras`,
  );
}

export async function getAllSourceFields(
  repoId: string,
): Promise<AvailableCustomField[]> {
  return await getAllCursorPaginatedItems<AvailableCustomField>(
    `/repos/${repoId}/logs/source`,
  );
}

export async function getAllResourceTypes(repoId: string): Promise<string[]> {
  return getNames(
    getAllCursorPaginatedItems<Name>(
      `/repos/${repoId}/logs/aggs/resources/types`,
      {},
    ),
  );
}

export async function getAllResourceCustomFields(
  repoId: string,
): Promise<AvailableCustomField[]> {
  return await getAllCursorPaginatedItems<AvailableCustomField>(
    `/repos/${repoId}/logs/resources/extras`,
  );
}

export async function getAllDetailFields(
  repoId: string,
): Promise<AvailableCustomField[]> {
  return await getAllCursorPaginatedItems<AvailableCustomField>(
    `/repos/${repoId}/logs/details`,
  );
}

export async function getAllTagTypes(repoId: string): Promise<string[]> {
  return getNames(
    getAllCursorPaginatedItems<Name>(
      `/repos/${repoId}/logs/aggs/tags/types`,
      {},
    ),
  );
}

export async function getAllAttachmentTypes(repoId: string): Promise<string[]> {
  return getNames(
    getAllCursorPaginatedItems<Name>(
      `/repos/${repoId}/logs/aggs/attachments/types`,
      {},
    ),
  );
}

export async function getAllAttachmentMimeTypes(
  repoId: string,
): Promise<string[]> {
  return getNames(
    getAllCursorPaginatedItems<Name>(
      `/repos/${repoId}/logs/aggs/attachments/mime-types`,
      {},
    ),
  );
}

export async function getActorNames(
  repoId: string,
  query: string,
): Promise<NameRefPair[]> {
  const { items } = await reqGet(`/repos/${repoId}/logs/aggs/actors/names`, {
    q: query,
  });
  return items;
}

export async function getResourceNames(
  repoId: string,
  query: string,
): Promise<NameRefPair[]> {
  const { items } = await reqGet(`/repos/${repoId}/logs/aggs/resources/names`, {
    q: query,
  });
  return items;
}

export async function getTagNames(
  repoId: string,
  query: string,
): Promise<NameRefPair[]> {
  const { items } = await reqGet(`/repos/${repoId}/logs/aggs/tags/names`, {
    q: query,
  });
  return items;
}

export async function getAllLogEntities(
  repoId: string,
  parentEntityRef?: string | null,
): Promise<LogEntity[]> {
  return getAllCursorPaginatedItems<LogEntity>(
    `/repos/${repoId}/logs/entities`,
    parentEntityRef ? { parentEntityRef: parentEntityRef } : { root: true },
  );
}

export async function getLogEntity(
  repoId: string,
  entityRef: string,
): Promise<LogEntity> {
  return await reqGet(`/repos/${repoId}/logs/entities/${entityRef}`);
}

export async function getActor(
  repoId: string,
  actorRef: string,
): Promise<Actor> {
  return await reqGet(`/repos/${repoId}/logs/actors/${actorRef}`);
}

export async function getResource(
  repoId: string,
  resourceRef: string,
): Promise<Resource> {
  return await reqGet(`/repos/${repoId}/logs/resources/${resourceRef}`);
}

export async function getTag(repoId: string, tagRef: string): Promise<Tag> {
  return await reqGet(`/repos/${repoId}/logs/tags/${tagRef}`);
}

async function getValues(promise: Promise<Value[]>): Promise<string[]> {
  return promise.then((values) => values.map((v) => v.value));
}

export async function getAllDetailFieldEnumValues(
  repoId: string,
  fieldName: string,
): Promise<string[]> {
  return getValues(
    getAllCursorPaginatedItems(
      `/repos/${repoId}/logs/details/${fieldName}/values`,
      {},
    ),
  );
}

export async function getAllSourceFieldEnumValues(
  repoId: string,
  fieldName: string,
): Promise<string[]> {
  return getValues(
    getAllCursorPaginatedItems(
      `/repos/${repoId}/logs/source/${fieldName}/values`,
      {},
    ),
  );
}

export async function getAllActorCustomFieldEnumValues(
  repoId: string,
  fieldName: string,
): Promise<string[]> {
  return getValues(
    getAllCursorPaginatedItems(
      `/repos/${repoId}/logs/actors/extras/${fieldName}/values`,
      {},
    ),
  );
}

export async function getAllResourceCustomFieldEnumValues(
  repoId: string,
  fieldName: string,
): Promise<string[]> {
  return getValues(
    getAllCursorPaginatedItems(
      `/repos/${repoId}/logs/resources/extras/${fieldName}/values`,
      {},
    ),
  );
}
