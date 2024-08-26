import { CurrentUserInfo } from "./api";

export function getUserHomeRoute(user: CurrentUserInfo): string {
  if (user.permissions.logs.read !== "none") {
    return "/logs";
  }
  if (user.permissions.management.users.read) {
    return "/users";
  }
  if (user.permissions.management.apikeys.read) {
    return "/apikeys";
  }
  if (user.permissions.management.repos.read) {
    return "/repos";
  }
  return "/";
}
