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
    return changeCase.snakeCase(column);
  });
}

export function unnormalizeFilterColumnsFromApi(columns: string[]): string[] {
  return columns.map((col) => changeCase.camelCase(col));
}
