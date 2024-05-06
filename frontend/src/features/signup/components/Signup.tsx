import { Button, Center, PasswordInput, Stack, TextInput } from "@mantine/core";
import { isNotEmpty, matchesField, useForm } from "@mantine/form";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

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

function SignupForm({
  form,
  onSave,
  error,
}: {
  form: ReturnType<typeof useSignupForm>;
  onSave: (password: string) => void;
  error: string;
}) {
  return (
    <Center>
      <form onSubmit={form.onSubmit((values) => onSave(values.password))}>
        <Stack w="25rem" p="1rem">
          <h1>Sign up !</h1>
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
          {error && <div>{error}</div>}
        </Stack>
      </form>
    </Center>
  );
}

export function Signup({}) {
  const { token } = useParams();
  const form = useSignupForm();
  const [signupDone, setSignupDone] = useState(false);
  const [signupError, setSignupError] = useState("");
  const { data, error, isPending } = useQuery({
    queryKey: ["signup", token],
    queryFn: () => getSignupInfo(token!),
  });
  const mutation = useMutation({
    mutationFn: (password: string) => setPassword(token!, password),
    onSuccess: () => setSignupDone(true),
    onError: (error) => setSignupError(error.message),
  });

  useEffect(() => {
    if (data) form.setValues(data);
  }, [data]);

  if (signupDone) {
    return (
      <Center>
        <h1>Signup successful!</h1>
      </Center>
    );
  }

  if (error && (error as AxiosError).response?.status === 404) {
    return (
      <Center>
        <h1>Invalid token</h1>
      </Center>
    );
  }

  return (
    <SignupForm form={form} onSave={mutation.mutate} error={signupError} />
  );
}
