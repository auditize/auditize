import { Box, Button, Center, Stack, TextInput, Title } from "@mantine/core";
import { isEmail, useForm } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { InlineErrorMessage } from "@/components/InlineErrorMessage";

import { logIn } from "../api";

export function LogInForm({ onLogged }: { onLogged: () => void }) {
  const form = useForm({
    mode: "uncontrolled",
    initialValues: {
      email: "",
      password: "",
    },

    validate: {
      email: isEmail("Invalid email"),
    },
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: (values: { email: string; password: string }) =>
      logIn(values.email, values.password),
    onSuccess: () => {
      onLogged();
      navigate("/logs");
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  return (
    <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
      <Center>
        <Stack align="center">
          <Title order={1}>Welcome on Auditize !</Title>
          <Title order={2}>Please enter you credentials to log-in.</Title>
          <Stack>
            <TextInput
              {...form.getInputProps("email")}
              key={form.key("email")}
              label="Email"
              placeholder="Enter your email"
            />
            <TextInput
              {...form.getInputProps("password")}
              key={form.key("password")}
              label="Password"
              placeholder="Enter your password"
              type="password"
            />
            <Button type="submit">Submit</Button>
            <InlineErrorMessage>{error}</InlineErrorMessage>
          </Stack>
        </Stack>
      </Center>
    </form>
  );
}