import { reqGet } from "@/utils/api";

export interface Info {
  auditizeVersion: string;
}

export async function getInfo(): Promise<Info> {
  return await reqGet("/info");
}
