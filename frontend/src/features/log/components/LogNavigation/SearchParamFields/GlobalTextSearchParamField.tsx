import { SearchInput } from "@/components/SearchInput";
import { LogSearchParams } from "@/features/log/LogSearchParams";

export function GlobalTextSearchParamField({
  searchParams,
  onChange,
  onSubmit,
}: {
  searchParams: LogSearchParams;
  onChange: (name: string, value: any) => void;
  onSubmit: () => void;
}) {
  return (
    <SearchInput
      value={searchParams.q}
      onChange={(value) => onChange("q", value)}
      onSubmit={onSubmit}
      inputSize="15"
    />
  );
}
