import * as changeCase from "change-case";
import * as changeKeys from "change-case/keys";

// change-case does not support infinite depth, so let's say that 999 is "infinite enough"
const INFINITE_DEPTH = 999;

// When splitting words (independently of the source case), change-case also splits
// on ".", which is annoying since we use "." in custom fields.
// That's why we implement our own split functions.

function splitCamelCase(input: string) {
  return input
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .toLowerCase()
    .split(" ");
}

function splitSnakeCase(input: string) {
  return input.split("_");
}

export function snakeCaseToCamelCaseString(input: string): string {
  return changeCase.camelCase(input, { split: splitSnakeCase });
}

export function camelCaseToSnakeCaseString(input: string): string {
  return changeCase.snakeCase(input, { split: splitCamelCase });
}

export function snakeCaseToCamelCaseObjectKeys(
  obj: object,
  depth = INFINITE_DEPTH,
): any {
  return changeKeys.camelCase(obj, depth, {
    split: splitSnakeCase,
  });
}

export function camelCaseToSnakeCaseObjectKeys(obj: object): any {
  return changeKeys.snakeCase(obj, INFINITE_DEPTH, {
    split: splitCamelCase,
  });
}
