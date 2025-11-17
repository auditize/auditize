import { FocusTrap, Input, TextInput, TextInputProps } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { ReactNode } from "react";

export function ClearableTextInput({
  value,
  onChange,
  rightSection,
  component,
  ...props
}: {
  value: string;
  onChange: (value: string) => void;
  rightSection?: ReactNode;
  component?: React.ComponentType<TextInputProps>;
} & Omit<
  TextInputProps,
  "value" | "onChange" | "rightSection" | "onFocus" | "onBlur"
>) {
  const [isFocused, { open: setFocusActive, close: setFocusInactive }] =
    useDisclosure(false);

  const InputComponent = component || TextInput;

  return (
    <FocusTrap active={isFocused}>
      <InputComponent
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
              style={value ? undefined : { display: "none" }}
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
