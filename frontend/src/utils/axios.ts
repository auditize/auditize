import axios from "axios";

export const axiosInstance = axios.create({
  baseURL: "/api",
  // Enable cross site cookies
  // FIXME: it should only be enabled for development
  withCredentials: true,
});

const latency_min = Number(import.meta.env.VITE_AXIOS_LATENCY_MIN);
const latency_max = Number(import.meta.env.VITE_AXIOS_LATENCY_MAX);

if (latency_min && latency_max) {
  // Simulate network latency
  axiosInstance.interceptors.request.use(
    (config) => {
      const delay =
        ((Math.random() * 10000) % (latency_max - latency_min)) + latency_min;

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
}

export function enableAccessTokenAuthentication(accessToken: string) {
  axiosInstance.defaults.headers.common["Authorization"] =
    `Bearer ${accessToken}`;
}

export function setBaseURL(baseURL: string) {
  axiosInstance.defaults.baseURL = baseURL + "/api";
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
