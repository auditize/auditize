import { Container } from "@mantine/core";
import { useSearchParams } from "react-router-dom";

import { deserializeDate, serializeDate } from "@/utils/date";

import { buildEmptyLogsFilterParams, LogsFilterParams } from "../api";
import { LogsFilter } from "./LogsFilter";
import { LogsLoader } from "./LogsLoader";

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
  };
}

function stripEmptyStringsFromObject(obj: any): any {
  // Make the query string prettier by avoid query keys without values
  return Object.fromEntries(
    Object.entries(obj).filter(([_, value]) => value !== ""),
  );
}

function filterToSearchParams(filter: LogsFilterParams): URLSearchParams {
  return new URLSearchParams(
    stripEmptyStringsFromObject({
      ...filter,
      since: filter.since ? serializeDate(filter.since) : "",
      until: filter.until ? serializeDate(filter.until) : "",
    }),
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
