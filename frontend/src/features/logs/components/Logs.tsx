import { Container } from '@mantine/core';
import { LogsFilterParams } from '../api';
import { LogsLoader } from './LogsLoader';
import { LogsFilter } from './LogsFilter';
import { useSearchParams } from 'react-router-dom';
import { deserializeDate, serializeDate } from '@/utils/date';

function searchParamsToFilter(params: URLSearchParams): LogsFilterParams {
  const obj = Object.fromEntries(params.entries());
  return {
    ...obj,
    since: obj.since ? deserializeDate(obj.since) : null,
    until: obj.until ? deserializeDate(obj.until) : null
  }
}

function stripEmptyStringsFromObject(obj: any): any {
  return Object.fromEntries(Object.entries(obj).filter(([_, value]) => value !== ""));
}

function filterToSearchParams(filter: LogsFilterParams): URLSearchParams {
  return new URLSearchParams(stripEmptyStringsFromObject({
    ...filter,
    since: filter.since ? serializeDate(filter.since) : "",
    until: filter.until ? serializeDate(filter.until) : ""
  }));
}

export function Logs() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filter = searchParamsToFilter(searchParams);

  return (
    <Container size="xl" p="20px">
      <LogsFilter params={filter} onChange={(newFilter) => setSearchParams(filterToSearchParams(newFilter))} />
      <LogsLoader filter={filter} onTableFilterChange={(name, value) => {
        setSearchParams((currentSearchParams) => {
          const currentFilter = searchParamsToFilter(currentSearchParams);
          const newFilter = {
            repoId: currentFilter.repoId, since: currentFilter.since, until: currentFilter.until,
            [name]: value
          };
          return filterToSearchParams(newFilter);
        })
      }}/>
    </Container>
  );
}
