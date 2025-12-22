import { DateTime } from "@/components/DateTime";
import { Log } from "@/features/log/api";

export function DateField({ log }: { log: Log }) {
  return (
    <DateTime
      value={log.emittedAt}
      textProps={{
        size: "xs",
        style: {
          fontVariantNumeric: "tabular-nums",
        },
      }}
      tooltip
    />
  );
}
