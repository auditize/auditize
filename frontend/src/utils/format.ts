export function labelize(s: string) {
  s = s.replace(/[._-]/g, ' ');
  return s.charAt(0).toUpperCase() + s.slice(1);
}