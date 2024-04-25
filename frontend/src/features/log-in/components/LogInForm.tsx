import { Center, Stack, TextInput, Button, Title, Box } from "@mantine/core";
import { useForm, isEmail } from '@mantine/form';
import { useMutation } from "@tanstack/react-query";
import { log_in } from "../api";
import { useState } from "react";
import { InlineErrorMessage } from "@/components/InlineErrorMessage";

export function LogInForm() {
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
  const [logged, setLogged] = useState(false);
  const [error, setError] = useState('');
  const mutation = useMutation({
    mutationFn: (values: {email: string, password: string}) => log_in(values.email, values.password),
    onSuccess: () => {
      setLogged(true);
    },
    onError: (error) => {
      setError(error.message);
    },
  })

  if (logged) {
    return (
      <Center>
        <Box>
          <Title order={1}>You are now logged in !</Title>
        </Box>
      </Center>
    );
  }

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