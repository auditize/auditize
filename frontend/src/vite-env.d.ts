/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WEBCO_REPO_ID: string;
  readonly VITE_WEBCO_ACCESS_TOKEN: string;
  readonly VITE_WEBCO_LANG: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
