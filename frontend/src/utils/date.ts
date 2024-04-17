import dayjs from "dayjs";


export function serializeDate(date: Date) {
  return dayjs(date).utc().format("YYYY-MM-DDTHH:mm:ss") + "Z";
}

export function deserializeDate(date: string) {
  return dayjs(date).toDate();
}