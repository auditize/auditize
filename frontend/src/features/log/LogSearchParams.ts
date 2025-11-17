import { deserializeDate, serializeDate } from "@/utils/date";
import { camelCaseToSnakeCaseObjectKeys } from "@/utils/switchCase";

export class LogSearchParams {
  repoId: string = "";
  q: string = "";
  actionCategory: string = "";
  actionType: string = "";
  actorType: string = "";
  actorName: string = "";
  actorRef: string = "";
  actorExtra: Map<string, string> = new Map();
  source: Map<string, string> = new Map();
  resourceType: string = "";
  resourceName: string = "";
  resourceRef: string = "";
  resourceExtra: Map<string, string> = new Map();
  details: Map<string, string> = new Map();
  tagRef: string = "";
  tagType: string = "";
  tagName: string = "";
  hasAttachment: boolean | undefined;
  attachmentName: string = "";
  attachmentType: string = "";
  attachmentMimeType: string = "";
  entityRef: string = "";
  since: Date | null = null;
  until: Date | null = null;

  constructor() {}

  isEmpty(): boolean {
    return [
      this.q,
      this.actionCategory,
      this.actionType,
      this.actorType,
      this.actorName,
      this.actorRef,
      this.actorExtra.size > 0,
      this.source.size > 0,
      this.resourceType,
      this.resourceName,
      this.resourceRef,
      this.resourceExtra.size > 0,
      this.details.size > 0,
      this.tagRef,
      this.tagType,
      this.tagName,
      this.hasAttachment,
      this.attachmentName,
      this.attachmentType,
      this.attachmentMimeType,
      this.entityRef,
      this.since,
      this.until,
    ].every((value) => !value);
  }

  static fromProperties(obj: object): LogSearchParams {
    return Object.assign(new LogSearchParams(), obj);
  }

  static #serializeCustomFields(
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

  serialize({
    includeRepoId = true,
    snakeCase = false,
  }: { includeRepoId?: boolean; snakeCase?: boolean } = {}): Record<
    string,
    any
  > {
    let serialized: Record<string, any> = {
      ...(includeRepoId ? { repoId: this.repoId } : {}),

      // Dates
      since: this.since ? serializeDate(this.since) : null,
      until: this.until ? serializeDate(this.until) : null,

      // Query (global text search)
      q: this.q,

      // Action
      actionCategory: this.actionCategory,
      actionType: this.actionType,

      // Actor
      actorType: this.actorType,
      actorName: this.actorName,
      actorRef: this.actorRef,
      ...LogSearchParams.#serializeCustomFields(this.actorExtra, "actor"),

      // Source
      ...LogSearchParams.#serializeCustomFields(this.source, "source"),

      // Resource
      resourceType: this.resourceType,
      resourceName: this.resourceName,
      resourceRef: this.resourceRef,
      ...LogSearchParams.#serializeCustomFields(this.resourceExtra, "resource"),

      // Details
      ...LogSearchParams.#serializeCustomFields(this.details, "details"),

      // Tag
      tagRef: this.tagRef,
      tagType: this.tagType,
      tagName: this.tagName,

      // Attachment
      hasAttachment: this.hasAttachment,
      attachmentName: this.attachmentName,
      attachmentType: this.attachmentType,
      attachmentMimeType: this.attachmentMimeType,

      // Entity
      entityRef: this.entityRef,
    };

    // Remove null and empty strings
    serialized = Object.fromEntries(
      Object.entries(serialized).filter(
        ([, value]) => value !== null && value !== undefined && value !== "",
      ),
    );

    // Snake case keys
    if (snakeCase) {
      serialized = camelCaseToSnakeCaseObjectKeys(serialized);
    }

    return serialized;
  }

  static #deserializeCustomFields(
    params: Record<string, string>,
    prefix: string,
  ): Map<string, string> {
    const customFields = new Map<string, string>();
    for (const [name, value] of Object.entries(params)) {
      const parts = name.split(".");
      if (parts.length === 2 && parts[0] === prefix) {
        customFields.set(parts[1], value);
      }
    }
    return customFields;
  }

  static deserialize(obj: Record<string, any>): LogSearchParams {
    const params = new LogSearchParams();
    params.repoId = obj.repoId ?? "";
    params.since = obj.since ? deserializeDate(obj.since) : null;
    params.until = obj.until ? deserializeDate(obj.until) : null;
    params.q = obj.q ?? "";
    params.actionCategory = obj.actionCategory ?? "";
    params.actionType = obj.actionType ?? "";
    params.actorType = obj.actorType ?? "";
    params.actorName = obj.actorName ?? "";
    params.actorRef = obj.actorRef ?? "";
    params.actorExtra = LogSearchParams.#deserializeCustomFields(obj, "actor");
    params.source = LogSearchParams.#deserializeCustomFields(obj, "source");
    params.resourceType = obj.resourceType ?? "";
    params.resourceName = obj.resourceName ?? "";
    params.resourceRef = obj.resourceRef ?? "";
    params.resourceExtra = LogSearchParams.#deserializeCustomFields(
      obj,
      "resource",
    );
    params.details = LogSearchParams.#deserializeCustomFields(obj, "details");
    params.tagRef = obj.tagRef ?? "";
    params.tagType = obj.tagType ?? "";
    params.tagName = obj.tagName ?? "";
    params.hasAttachment =
      typeof obj.hasAttachment === "boolean"
        ? obj.hasAttachment ?? undefined
        : obj.hasAttachment === "true"
          ? true
          : undefined;
    params.attachmentName = obj.attachmentName ?? "";
    params.attachmentType = obj.attachmentType ?? "";
    params.attachmentMimeType = obj.attachmentMimeType ?? "";
    params.entityRef = obj.entityRef ?? "";
    return params;
  }
}
