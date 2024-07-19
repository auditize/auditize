import * as changeCase from "change-case";

import { sortFields } from "../logs/components/LogTable";

export function normalizeFilterColumnsForApi(columns: string[]): string[] {
  return columns.toSorted(sortFields).map((column) => {
    if (column.includes(".")) {
      // make a special case for custom fields (that contains ".") because
      // changeCase.snakeCase transforms "." to "_"
      // it assumes that the custom field group is all lowercase (which is currently true:
      // actor, source, resource, details)
      return column;
    }
    if (column === "date") {
      return "saved_at";
    }
    return changeCase.snakeCase(column);
  });
}

export function unnormalizeFilterColumnsFromApi(columns: string[]): string[] {
  return columns.map((column) => {
    if (column === "saved_at") {
      return "date";
    }
    return changeCase.camelCase(column);
  });
}
