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

export function unnormalizeFilterColumnsFromApi(columns: string[]): string[] {
  return columns.map((col) => snakeCaseToCamelCaseString(col));
}
