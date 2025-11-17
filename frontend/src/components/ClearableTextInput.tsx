import { FocusTrap, Input, TextInput, TextInputProps } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { ReactNode } from "react";

export function ClearableTextInput({
  value,
  onChange,
  rightSection,
  ...props
}: {
  value: string;
  onChange: (value: string) => void;
  rightSection?: ReactNode;
} & Omit<
  TextInputProps,
  "value" | "onChange" | "rightSection" | "onFocus" | "onBlur"
>) {
  const [isFocused, { open: setFocusActive, close: setFocusInactive }] =
    useDisclosure(false);

  return (
    <FocusTrap active={isFocused}>
      <TextInput
        onFocus={setFocusActive}
        onBlur={setFocusInactive}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        rightSection={
          value || !rightSection ? (
            <Input.ClearButton
              onClick={() => {
                onChange("");
                setFocusActive();
              }}
              style={{
                display: value ? undefined : "none",
              }}
            />
          ) : (
            rightSection
          )
        }
        {...props}
      />
    </FocusTrap>
  );
}
