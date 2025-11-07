import { DateTime } from "@/components/DateTime";
import { Log } from "@/features/log/api";

export function DateField({ log }: { log: Log }) {
  return (
    <DateTime
      value={log.savedAt}
      textProps={{
        size: "xs",
      }}
      tooltip
    />
  );
}
