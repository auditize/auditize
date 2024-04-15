import { Location } from "react-router-dom";

export function addQueryParamToLocation(location: Location, param: string, value: string) {
  const params = new URLSearchParams(location.search);
  params.set(param, value);
  return `${location.pathname}?${params.toString()}`;
}
