import { IconStar, IconStarFilled } from "@tabler/icons-react";

export function LogFilterFavoriteIcon({
  value,
  style,
}: {
  value: boolean;
  style?: React.CSSProperties;
}) {
  return value ? (
    <IconStarFilled style={style} color="var(--mantine-color-yellow-3)" />
  ) : (
    <IconStar style={style} color="var(--mantine-color-gray-3)" />
  );
}
