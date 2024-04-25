import axios from 'axios';

export const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000',
  // Enable cross site cookies
  // FIXME: it should only be enabled for development
  withCredentials: true,
});

// Simulate network latency
axiosInstance.interceptors.request.use(config => {
  const delay = Math.random() * 1000 % 200 + 100;  // Random delay between 100 and 300 ms

  return new Promise(resolve => setTimeout(() => {
    resolve(config);
  }, delay));
}, error => {
  return Promise.reject(error);
});
