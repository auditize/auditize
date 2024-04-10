import { Select } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { labelize } from '../utils/format';

export function PaginatedSelector(
  { label, queryKey, queryFn, selectedItem, onChange }: { label: string; queryKey: any; queryFn: () => Promise<string[]>; selectedItem?: string; onChange: (value: string) => void; }) {
  const { isPending, error, data } = useQuery({
    queryKey: queryKey,
    queryFn: queryFn,
    refetchOnWindowFocus: false
  });

  if (error)
    return <div>Error: {error.message}</div>;

  return (
    <Select
      data={data?.map((item) => ({ label: labelize(item), value: item }))}
      value={selectedItem || null}
      onChange={(value) => onChange(value || "")}
      placeholder={isPending ? "Loading..." : label}
      clearable
      display="flex"
      comboboxProps={{ withinPortal: false }} />
  );
}
