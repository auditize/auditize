import {
  camelCaseToSnakeCaseString,
  snakeCaseToCamelCaseString,
} from "@/utils/switchCase";

import { sortLogFields } from "../log/components/LogTable";

export function normalizeFilterColumnsForApi(columns: string[]): string[] {
  return columns
    .toSorted(sortLogFields)
    .map((col) => camelCaseToSnakeCaseString(col));
}

export function normalizeLogFieldNameFromApi(fieldName: string): string {
  return fieldName.match(/^(source|resource|details|actor)\./)
    ? fieldName
    : snakeCaseToCamelCaseString(fieldName);
}

export function unnormalizeFilterColumnsFromApi(columns: string[]): string[] {
  return columns.map(normalizeLogFieldNameFromApi);
}
