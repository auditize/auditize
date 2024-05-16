import { MultiSelect, TextInput } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";

export function CustomFieldSelector({
  label,
  queryKey,
  queryFn,
  enabled = true,
  value,
  onChange,
  itemLabel,
}: {
  label: string;
  queryKey: any;
  queryFn: () => Promise<any[]>;
  enabled?: boolean;
  value: Map<string, string>;
  onChange: (value: Map<string, string>) => void;
  itemLabel: (item: any) => string;
}) {
  const { isPending, error, data } = useQuery({
    queryKey: queryKey,
    queryFn: queryFn,
    enabled: enabled,
  });

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <>
      <MultiSelect
        data={data?.map((item) => ({
          label: itemLabel(item),
          value: item,
        }))}
        value={Array.from(value.keys()).sort()}
        onChange={(items) =>
          onChange(new Map(items.map((item) => [item, value.get(item) || ""])))
        }
        placeholder={isPending ? "Loading..." : label}
        display="flex"
        comboboxProps={{ position: "top", withinPortal: false }}
      />
      {Array.from(value.keys())
        .sort()
        .map((fieldName) => (
          <TextInput
            key={fieldName}
            placeholder={itemLabel(fieldName)}
            value={value.get(fieldName)}
            onChange={(event) =>
              onChange(
                new Map([...value, [fieldName, event.currentTarget.value]]),
              )
            }
          />
        ))}
    </>
  );
}
