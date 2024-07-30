/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WEBCO_REPO_ID: string;
  readonly VITE_WEBCO_ACCESS_TOKEN: string;
  readonly VITE_WEBCO_LANG: string;
  readonly VITE_AXIOS_LATENCY_MIN: string;
  readonly VITE_AXIOS_LATENCY_MAX: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
