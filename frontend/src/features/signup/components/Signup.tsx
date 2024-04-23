import { useForm, isNotEmpty, matchesField } from '@mantine/form';
import { PasswordInput, TextInput, Button, Stack, Center } from '@mantine/core';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getSignupInfo, setPassword } from '../api';
import { useEffect, useState } from 'react';
import {AxiosError} from 'axios';

export function Signup({}) {
  const {token} = useParams();
  const form = useForm({
    mode: 'uncontrolled',
    initialValues: {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      passwordConfirmation: '',
    },
    validate: {
      password: isNotEmpty('Password is required'),
      passwordConfirmation: matchesField('password', 'Passwords do not match'),
    }
  });
  const [signupDone, setSignupDone] = useState(false);
  const [signupError, setSignupError] = useState('');
  const {data, error, isPending} = useQuery({
    queryKey: ['signup', token],
    queryFn: () => getSignupInfo(token!),
  });
  const mutation = useMutation({
    mutationFn: (password: string) => setPassword(token!, password),
    onSuccess: () => setSignupDone(true),
    onError: (error) => setSignupError(error.message),
  });

  useEffect(() => {
    if (data)
      form.setValues(data);
  }, [data]);

  if (signupDone) {
    return <Center><h1>Signup successful!</h1></Center>;
  }

  if (error && (error as AxiosError).response?.status === 404) {
    return <Center><h1>Invalid token</h1></Center>;
  }

  return (
    <Center>
      <form onSubmit={form.onSubmit((values) => mutation.mutate(values.password))}>
        <Stack w="25rem" p="1rem">
          <h1>Sign up !</h1>
          <TextInput
            {...form.getInputProps('firstName')}
            label="First name"
            key={form.key('firstName')}
            disabled
          />
          <TextInput
            {...form.getInputProps('lastName')}
            label="Last name"
            key={form.key('lastName')}
            disabled
          />
          <TextInput
            {...form.getInputProps('email')}
            key={form.key('email')}
            label="Email"
            disabled
          />
          <PasswordInput
            {...form.getInputProps('password')}
            label="Password"
            placeholder='Password'
            key={form.key('password')}
          />
          <PasswordInput
            {...form.getInputProps('passwordConfirmation')}
            label="Password confirmation"
            placeholder='Password confirmation'
            key={form.key('passwordConfirmation')}
          />
          <Button type='submit'>Submit</Button>
          {signupError && <div>{signupError}</div>}
        </Stack>
      </form>
    </Center>
  )
}