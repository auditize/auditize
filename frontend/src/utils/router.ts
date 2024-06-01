import { Location } from "react-router-dom";

export function addQueryParamToLocation(
  location: Location,
  param: string,
  value?: string,
): string {
  const params = new URLSearchParams(location.search);
  params.set(param, value || "");

  // Remove trailing "=" if any to get a nicer URL
  let queryString = params.toString();
  if (queryString.endsWith("=")) {
    queryString = queryString.slice(0, -1);
  }

  return `${location.pathname}?${queryString}`;
}
