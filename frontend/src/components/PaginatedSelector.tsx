import { Select } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { SelectWithoutDropdown } from "./SelectWithoutDropdown";

// FIXME: refactor PaginatedSelector & PaginatedSelectorWithoutDropdown

export function PaginatedSelector({
  label,
  queryKey,
  queryFn,
  enabled = true,
  onDataLoaded,
  selectedItem,
  clearable = true,
  onChange,
  itemLabel,
  itemValue,
}: {
  label: string;
  queryKey: any;
  queryFn: () => Promise<any[]>;
  enabled?: boolean;
  onDataLoaded?: (data: any[]) => void;
  selectedItem?: string;
  clearable?: boolean;
  onChange: (value: string) => void;
  itemLabel: (item: any) => string;
  itemValue: (item: any) => string;
}) {
  const { isPending, error, data } = useQuery({
    queryKey: queryKey,
    queryFn: queryFn,
    enabled: enabled,
  });

  useEffect(() => {
    if (data && onDataLoaded) onDataLoaded(data);
  }, [data, selectedItem]);

  if (error) return <div>Error: {error.message}</div>;

  return (
    <Select
      data={data?.map((item) => ({
        label: itemLabel(item),
        value: itemValue(item),
      }))}
      value={selectedItem || null}
      onChange={(value) => onChange(value || "")}
      placeholder={isPending ? "Loading..." : label}
      clearable={clearable}
      display="flex"
      comboboxProps={{ withinPortal: false }}
    />
  );
}

function PaginatedSelectorWithoutDropdown({
  label,
  queryKey,
  queryFn,
  enabled = true,
  onDataLoaded,
  selectedItem,
  onChange,
  itemLabel,
  itemValue,
}: {
  label: string;
  queryKey: any;
  queryFn: () => Promise<any[]>;
  enabled?: boolean;
  onDataLoaded?: (data: any[]) => void;
  selectedItem?: string;
  onChange: (value: string) => void;
  itemLabel: (item: any) => string;
  itemValue: (item: any) => string;
}) {
  const { isPending, error, data } = useQuery({
    queryKey: queryKey,
    queryFn: queryFn,
    enabled: enabled,
  });

  useEffect(() => {
    if (data && onDataLoaded) onDataLoaded(data);
  }, [data, selectedItem]);

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <SelectWithoutDropdown
      data={
        data
          ? data.map((item) => ({
              label: itemLabel(item),
              value: itemValue(item),
            }))
          : []
      }
      value={selectedItem || ""}
      onChange={(value) => onChange(value || "")}
      placeholder={isPending ? "Loading..." : label}
    />
  );
}

PaginatedSelector.WithoutDropdown = PaginatedSelectorWithoutDropdown;
