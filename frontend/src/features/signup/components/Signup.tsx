import {
  Anchor,
  Button,
  Center,
  PasswordInput,
  Stack,
  TextInput,
  Title,
} from "@mantine/core";
import { isNotEmpty, matchesField, useForm } from "@mantine/form";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import React, { useEffect } from "react";
import { NavLink, useParams } from "react-router-dom";

import { InlineErrorMessage } from "@/components/InlineErrorMessage";
import Message from "@/components/Message";

import { getSignupInfo, setPassword } from "../api";

function useResetPasswordForm() {
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
  successMessage: React.ReactNode;
}) {
  const { token } = useParams();
  const form = useResetPasswordForm();
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

  const disabledForm =
    query.isLoading || mutation.isPending || mutation.isSuccess;

  return (
    <Center>
      <form
        onSubmit={form.onSubmit((values) => mutation.mutate(values.password))}
      >
        <Stack w="25rem" p="1rem" pt="3rem">
          <Title order={1} ta="center">
            {title}
          </Title>
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
            disabled={disabledForm}
          />
          <PasswordInput
            {...form.getInputProps("passwordConfirmation")}
            label="Password confirmation"
            placeholder="Password confirmation"
            key={form.key("passwordConfirmation")}
            disabled={disabledForm}
          />
          <Button type="submit" disabled={disabledForm}>
            Submit
          </Button>
          <InlineErrorMessage>{mutation.error}</InlineErrorMessage>
        </Stack>
        {mutation.isSuccess && (
          <Message.Success>
            <>
              {successMessage} <br />
              You can now log in by&nbsp;
              <Anchor component={NavLink} to="/login">
                clicking on this link
              </Anchor>
              .
            </>
          </Message.Success>
        )}
      </form>
    </Center>
  );
}

export function Signup() {
  return (
    <BaseResetPassword
      title="Signup !"
      successMessage="The setup of your user account is now complete."
    />
  );
}

export function ResetPassword() {
  return (
    <BaseResetPassword
      title="Reset your password"
      successMessage="Your password has been successfully updated."
    />
  );
}
