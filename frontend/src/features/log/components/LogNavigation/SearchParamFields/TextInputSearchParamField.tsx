import { LogSearchParams } from "@/features/log/LogSearchParams";

import { BaseTextInputSearchParamField } from "./BaseTextInputSearchParamField";

export function TextInputSearchParamField({
  label,
  searchParams,
  searchParamName,
  openedByDefault,
  onChange,
  onRemove,
  onSubmit,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
}) {
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;
  return (
    <BaseTextInputSearchParamField
      label={label}
      name={searchParamName}
      value={value}
      openedByDefault={openedByDefault}
      onChange={(value) => onChange(searchParamName, value)}
      onRemove={onRemove}
      onSubmit={onSubmit}
    />
  );
}
