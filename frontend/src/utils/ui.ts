import { rem } from "@mantine/core";
import type * as CSS from "csstype";

export function iconSize(size: any) {
  return { width: rem(size), height: rem(size) };
}

export function iconBesideText({
  size,
  top,
  marginRight,
}: {
  size: CSS.StandardProperties["width"];
  top?: CSS.StandardProperties["top"];
  marginRight?: CSS.StandardProperties["marginRight"];
}): CSS.Properties {
  return {
    ...iconSize(size),
    position: "relative",
    top: top,
    marginRight: marginRight,
  };
}
