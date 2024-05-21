import { Button, Center, Stack, TextInput, Title } from "@mantine/core";
import { isEmail, useForm } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { InlineErrorMessage } from "@/components/InlineErrorMessage";

import { CurrentUserInfo, logIn } from "../api";
import { useCurrentUser } from "../contexts";

export function LogInForm({
  onLogged,
}: {
  onLogged: (user: CurrentUserInfo) => void;
}) {
  const { isAuthenticated } = useCurrentUser();
  const [searchParams] = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/logs";
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
    onSuccess: (user) => {
      onLogged(user);
      navigate(decodeURIComponent(redirectTo), { replace: true });
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  return (
    <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
      <Center pt="4rem">
        <Stack align="center">
          <Title order={1}>Welcome on Auditize</Title>
          <Stack pt="1rem" gap="1.25rem">
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
            <Button type="submit">Sign in</Button>
            <InlineErrorMessage>{error}</InlineErrorMessage>
          </Stack>
        </Stack>
      </Center>
    </form>
  );
}
