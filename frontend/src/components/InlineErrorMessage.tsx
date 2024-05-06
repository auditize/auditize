export function InlineErrorMessage({ children }: { children: any }) {
  if (!children) return null;

  return <span>{children}</span>;
}
