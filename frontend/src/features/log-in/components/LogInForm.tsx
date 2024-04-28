import { Center, Stack, TextInput, Button, Title, Box } from "@mantine/core";
import { useForm, isEmail } from '@mantine/form';
import { useMutation } from "@tanstack/react-query";
import { log_in } from "../api";
import { useState } from "react";
import { InlineErrorMessage } from "@/components/InlineErrorMessage";
import { useNavigate } from "react-router-dom";

export function LogInForm({onLogged}: {onLogged: () => void}) {
  const form = useForm({
    mode: 'uncontrolled',
    initialValues: {
      email: '',
      password: '',
    },

    validate: {
      email: isEmail('Invalid email'),
    },
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: (values: {email: string, password: string}) => log_in(values.email, values.password),
    onSuccess: () => {
      onLogged();
      navigate('/logs');
    },
    onError: (error) => {
      setError(error.message);
    },
  })

  return (
    <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
      <Center>
          <Stack align='center'>
            <Title order={1}>Welcome on Auditize !</Title>
            <Title order={2}>Please enter you credentials to log-in.</Title>
            <Stack>
              <TextInput
                {...form.getInputProps('email')} key={form.key('email')}
                label="Email" placeholder="Enter your email"
              />
              <TextInput
                {...form.getInputProps('password')} key={form.key('password')}
                label="Password" placeholder="Enter your password" type="password"
              />
              <Button type="submit">Submit</Button>
              <InlineErrorMessage>{error}</InlineErrorMessage>
            </Stack>
          </Stack>
        </Center>
      </form>
  );
}