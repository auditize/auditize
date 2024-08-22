import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { getAllPagePaginatedItems, reqGet } from "@/utils/api";

import { LogSearchParams } from "./LogSearchParams";

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

export async function getAllLogEntities(
  repoId: string,
  parentEntityRef?: string | null,
): Promise<LogEntity[]> {
  return getAllPagePaginatedItems<LogEntity>(
    `/repos/${repoId}/logs/entities`,
    parentEntityRef ? { parentEntityRef: parentEntityRef } : { root: true },
  );
}

export async function getLogEntity(
  repoId: string,
  entityRef: string,
): Promise<LogEntity> {
  return await reqGet(`/repos/${repoId}/logs/entities/ref:${entityRef}`);
}
