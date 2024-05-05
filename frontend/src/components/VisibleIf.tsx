export function VisibleIf({ condition, children } : { condition: boolean | null, children: React.ReactNode }) {
  return condition ? children : null;
}
