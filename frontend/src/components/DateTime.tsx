import { Text, TextProps, Tooltip } from "@mantine/core";
import dayjs from "dayjs";
import "dayjs/locale/fr";
import localizedFormat from "dayjs/plugin/localizedFormat";

import { useI18nContext } from "@/i18n";

dayjs.extend(localizedFormat);

export function DateTime({
  value,
  textProps,
  tooltip = false,
}: {
  value: string;
  textProps?: TextProps;
  tooltip?: boolean;
}) {
  const { lang } = useI18nContext();
  const date = (
    <Text span size="sm" {...textProps}>
      {dayjs(value).format("YYYY-MM-DD HH:mm")}
    </Text>
  );

  if (!tooltip) {
    return date;
  }

  const format =
    lang === "en"
      ? "dddd, MMMM D, YYYY h:mm:ss A"
      : lang === "fr"
        ? "dddd D MMMM YYYY, HH:mm:ss"
        : "LLLL";
  return (
    <Tooltip
      label={dayjs(value).locale(lang).format(format)}
      withinPortal={false}
    >
      {date}
    </Tooltip>
  );
}
