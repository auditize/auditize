import { useState } from 'react';
import { Container } from '@mantine/core';
import { LogsFilterParams } from '../api';
import { LogsLoader } from './LogsLoader';
import { LogsFilter } from './LogsFilter';
import { buildEmptyLogsFilterParams } from '../api';

export function Logs() {
  const [filter, setFilter] = useState<LogsFilterParams>(buildEmptyLogsFilterParams());

  return (
    <Container size="xl" p="20px">
      <LogsFilter params={filter} onChange={setFilter} />
      <LogsLoader filter={filter} onTableFilterChange={(name, value) => {
        setFilter((filter) => ({since: filter.since, until: filter.until, [name]: value}));
      }}/>
    </Container>
  );
}
