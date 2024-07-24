import {
  camelCaseToSnakeCaseString,
  snakeCaseToCamelCaseString,
} from "@/utils/switchCase";

import { sortFields } from "../logs/components/LogTable";

export function normalizeFilterColumnsForApi(columns: string[]): string[] {
  return columns
    .toSorted(sortFields)
    .map((col) => camelCaseToSnakeCaseString(col));
}

export function unnormalizeFilterColumnsFromApi(columns: string[]): string[] {
  return columns.map((col) => snakeCaseToCamelCaseString(col));
}
