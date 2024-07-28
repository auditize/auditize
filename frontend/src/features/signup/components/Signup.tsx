import { Button, Center, PasswordInput, Stack, TextInput } from "@mantine/core";
import { isNotEmpty, matchesField, useForm } from "@mantine/form";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useEffect } from "react";
import { useParams } from "react-router-dom";

import { InlineErrorMessage } from "@/components/InlineErrorMessage";

import { getSignupInfo, setPassword } from "../api";

function useSignupForm() {
  return useForm({
    mode: "uncontrolled",
    initialValues: {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      passwordConfirmation: "",
    },
    validate: {
      password: isNotEmpty("Password is required"),
      passwordConfirmation: matchesField("password", "Passwords do not match"),
    },
  });
}

function BaseResetPassword({
  title,
  successMessage,
}: {
  title: string;
  successMessage: string;
}) {
  const { token } = useParams();
  const form = useSignupForm();
  const query = useQuery({
    queryKey: ["signup", token],
    queryFn: () => getSignupInfo(token!),
  });
  const mutation = useMutation({
    mutationFn: (password: string) => setPassword(token!, password),
  });

  useEffect(() => {
    if (query.data) {
      form.setValues(query.data);
    }
  }, [query.data]);

  if ((query?.error as AxiosError)?.response?.status === 404) {
    return (
      <Center>
        <h1>Invalid token</h1>
      </Center>
    );
  }

  if (mutation.isSuccess) {
    return (
      <Center>
        <h1>{successMessage}</h1>
      </Center>
    );
  }

  return (
    <Center>
      <form
        onSubmit={form.onSubmit((values) => mutation.mutate(values.password))}
      >
        <Stack w="25rem" p="1rem">
          <h1>{title}</h1>
          <TextInput
            {...form.getInputProps("firstName")}
            label="First name"
            key={form.key("firstName")}
            disabled
          />
          <TextInput
            {...form.getInputProps("lastName")}
            label="Last name"
            key={form.key("lastName")}
            disabled
          />
          <TextInput
            {...form.getInputProps("email")}
            key={form.key("email")}
            label="Email"
            disabled
          />
          <PasswordInput
            {...form.getInputProps("password")}
            label="Password"
            placeholder="Password"
            key={form.key("password")}
          />
          <PasswordInput
            {...form.getInputProps("passwordConfirmation")}
            label="Password confirmation"
            placeholder="Password confirmation"
            key={form.key("passwordConfirmation")}
          />
          <Button type="submit">Submit</Button>
          <InlineErrorMessage>{mutation.error}</InlineErrorMessage>
        </Stack>
      </form>
    </Center>
  );
}

export function Signup() {
  return (
    <BaseResetPassword title="Signup !" successMessage="Signup successful !" />
  );
}

export function ResetPassword() {
  return (
    <BaseResetPassword
      title="Reset your password"
      successMessage="Your password has been successfully reset"
    />
  );
}
