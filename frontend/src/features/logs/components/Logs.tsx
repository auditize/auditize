import { Container } from "@mantine/core";
import { useSearchParams } from "react-router-dom";

import { deserializeDate } from "@/utils/date";

import {
  buildEmptyLogsFilterParams,
  LogsFilterParams,
  prepareLogFilterForApi,
} from "../api";
import { LogsFilter } from "./LogsFilter";
import { LogsLoader } from "./LogsLoader";

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

function searchParamsToFilter(params: URLSearchParams): LogsFilterParams {
  // filter the params from the LogsFilterParams available keys (white list)
  // in order to avoid possible undesired keys in LogsFilterParams resulting object
  const template = buildEmptyLogsFilterParams();
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
  };
}

function stripEmptyStringsFromObject(obj: any): any {
  // Make the query string prettier by avoid query keys without values
  return Object.fromEntries(
    Object.entries(obj).filter(([_, value]) => (value !== "" && value !== undefined)), // prettier-ignore
  );
}

function filterToSearchParams(filter: LogsFilterParams): URLSearchParams {
  return new URLSearchParams(
    stripEmptyStringsFromObject(prepareLogFilterForApi(filter)),
  );
}

export function Logs() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filter = searchParamsToFilter(searchParams);

  return (
    <Container size="xl" p="20px">
      <LogsFilter
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
      <LogsLoader
        filter={filter}
        onTableFilterChange={(name, value) => {
          setSearchParams((currentSearchParams) => {
            const currentFilter = searchParamsToFilter(currentSearchParams);
            const newFilter = {
              repoId: currentFilter.repoId,
              since: currentFilter.since,
              until: currentFilter.until,
              [name]: value,
            };
            return filterToSearchParams(newFilter);
          });
        }}
      />
    </Container>
  );
}
