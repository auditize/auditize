export function titlize(s: string) {
  s = s.replace(/[._-]/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function labelize(s: string) {
  return s.replace(/[._-]/g, " ");
}
