import axios from "axios";

export const axiosInstance = axios.create({
  baseURL: "/api",
  // Enable cross site cookies
  // FIXME: it should only be enabled for development
  withCredentials: true,
});

// Simulate network latency
axiosInstance.interceptors.request.use(
  (config) => {
    const delay = ((Math.random() * 1000) % 200) + 100; // Random delay between 100 and 300 ms

    return new Promise((resolve) =>
      setTimeout(() => {
        resolve(config);
      }, delay),
    );
  },
  (error) => {
    return Promise.reject(error);
  },
);

export function enableAccessTokenAuthentication(accessToken: string) {
  axiosInstance.defaults.headers.common["Authorization"] =
    `Bearer ${accessToken}`;
}

export function interceptStatusCode(
  statusCode: number,
  func: (error: any) => void,
) {
  const interceptor = axiosInstance.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      if (error.response.status === statusCode) {
        func(error);
      }
      return Promise.reject(new Error(error.response.data.message));
    },
  );
  return () => {
    axiosInstance.interceptors.response.eject(interceptor);
  };
}
