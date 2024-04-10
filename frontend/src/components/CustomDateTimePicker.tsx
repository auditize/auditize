import { useEffect, useRef } from 'react';
import { DateTimePicker } from '@mantine/dates';

export function CustomDateTimePicker(
  { placeholder, value, onChange, initToEndOfDay = false }: { placeholder: string; value: Date | null | undefined; onChange: (value: Date | null) => void; initToEndOfDay?: boolean; }) {
  const previousValueRef = useRef<Date | null>(null);

  useEffect(() => {
    if (initToEndOfDay) {
      if (previousValueRef.current === null && value) {
        const date = new Date(value as Date);
        date.setHours(23, 59, 59);
        onChange(date);
      }
      previousValueRef.current = value || null;
    }
  });

  return (
    <DateTimePicker
      placeholder={placeholder}
      value={value}
      valueFormat='YYYY-MM-DD HH:mm'
      onChange={onChange}
      clearable
      w="14rem"
      popoverProps={{ withinPortal: false }} />
  );
}