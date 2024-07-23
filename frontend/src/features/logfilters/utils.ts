import * as changeCase from "change-case";

import { sortFields } from "../logs/components/LogTable";

// Make a special case for custom fields (that contains a ".") because
// changeCase treats "." as "_" (and we don't want that)
// it assumes that the custom field group is all lowercase (which is currently true:
// actor, source, resource, details)

export function normalizeFilterColumnsForApi(columns: string[]): string[] {
  return columns
    .toSorted(sortFields)
    .map((col) => (col.includes(".") ? col : changeCase.snakeCase(col)));
}

export function unnormalizeFilterColumnsFromApi(columns: string[]): string[] {
  return columns.map((col) =>
    col.includes(".") ? col : changeCase.camelCase(col),
  );
}
