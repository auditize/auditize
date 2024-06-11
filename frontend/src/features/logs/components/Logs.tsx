import { Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import { deserializeDate } from "@/utils/date";

import {
  buildLogSearchParams,
  LogSearchParams,
  prepareLogFilterForApi,
} from "../api";
import { LogFilter } from "./LogFilter";
import { LogLoader } from "./LogLoader";

function extractCustomFieldsFromSearchParams(
  params: URLSearchParams,
  prefix: string,
): Map<string, string> {
  const regexp = new RegExp(`^${prefix}\\[(.+)\\]$`);
  const customFields = new Map<string, string>();
  for (const [name, value] of params.entries()) {
    const match = name.match(regexp);
    if (match) {
      customFields.set(match[1], value);
    }
  }
  return customFields;
}

function searchParamsToFilter(params: URLSearchParams): LogSearchParams {
  // filter the params from the LogsFilterParams available keys (white list)
  // in order to avoid possible undesired keys in LogsFilterParams resulting object
  const template = buildLogSearchParams();
  const obj = Object.fromEntries(
    Object.keys(template).map((key) => [key, params.get(key) || ""]),
  );
  return {
    ...obj,
    since: obj.since ? deserializeDate(obj.since) : null,
    until: obj.until ? deserializeDate(obj.until) : null,
    actorExtra: extractCustomFieldsFromSearchParams(params, "actor"),
    resourceExtra: extractCustomFieldsFromSearchParams(params, "resource"),
    source: extractCustomFieldsFromSearchParams(params, "source"),
    details: extractCustomFieldsFromSearchParams(params, "details"),
  } as LogSearchParams;
}

function stripEmptyStringsFromObject(obj: any): any {
  // Make the query string prettier by avoid query keys without values
  return Object.fromEntries(
    Object.entries(obj).filter(([_, value]) => (value !== "" && value !== undefined)), // prettier-ignore
  );
}

function filterToSearchParams(filter: LogSearchParams): URLSearchParams {
  return new URLSearchParams(
    stripEmptyStringsFromObject(prepareLogFilterForApi(filter)),
  );
}

export function Logs() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const filter = searchParamsToFilter(searchParams);
  useDocumentTitle(t("log.list.documentTitle"));

  return (
    <Stack gap="lg" pt="xs">
      <LogFilter
        params={filter}
        onChange={(newFilter) => {
          // Do not keep the "repo auto-select redirect" in the history,
          // so the user can still go back to the previous page
          const isAutoSelectRepo = !!(!filter.repoId && newFilter.repoId);
          setSearchParams(filterToSearchParams(newFilter), {
            replace: isAutoSelectRepo,
          });
        }}
      />
      <LogLoader
        filter={filter}
        onTableFilterChange={(name, value) => {
          setSearchParams((currentSearchParams) => {
            const currentFilter = searchParamsToFilter(currentSearchParams);
            const newFilter = {
              ...buildLogSearchParams(),
              repoId: currentFilter.repoId,
              since: currentFilter.since,
              until: currentFilter.until,
              [name]: value,
            };
            return filterToSearchParams(newFilter);
          });
        }}
      />
    </Stack>
  );
}
