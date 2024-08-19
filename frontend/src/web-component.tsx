import { MantineProvider } from "@mantine/core";
import mantineCss from "@mantine/core/styles.layer.css?inline";
import mantineDateCss from "@mantine/dates/styles.layer.css?inline";
import { QueryClientProvider } from "@tanstack/react-query";
import datatableCss from "mantine-datatable/styles.layer.css?inline";
import React from "react";
import ReactDOM from "react-dom/client";
import rsuiteCss from "rsuite/dist/rsuite-no-reset.min.css?inline";

import { theme } from "@/theme";

import { LogNavigationStateProvider, Logs } from "./features/log";
import { I18nProvider } from "./i18n";
import layersCss from "./layers.css?inline";
import { enableAccessTokenAuthentication, setBaseURL } from "./utils/axios";
import { auditizeQueryClient } from "./utils/query";
import webComponentCss from "./web-component.css?inline";

function AccessTokenAuthProvider({
  accessTokenProvider,
  refreshInterval,
  children,
}: {
  accessTokenProvider: () => Promise<string>;
  refreshInterval: number;
  children: React.ReactNode;
}) {
  const [authenticated, setAuthenticated] = React.useState(false);
  const authenticate = () =>
    accessTokenProvider().then((token) =>
      enableAccessTokenAuthentication(token),
    );

  React.useEffect(() => {
    authenticate().then(() => {
      setAuthenticated(true);
      setInterval(() => authenticate(), refreshInterval);
    });
  }, []);

  if (authenticated) {
    return children;
  }
}

class LogWebComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  connectedCallback() {
    /*
     * Get the web component configuration from attributes
     */
    const repoId = this.getAttribute("repo-id");
    if (!repoId) {
      throw new Error("repo-id attribute is missing");
    }

    const accessTokenProviderFnName = this.getAttribute(
      "access-token-provider",
    );
    if (!accessTokenProviderFnName) {
      throw new Error("access-token-provider attribute is missing");
    }
    const accessTokenProvider = window[
      accessTokenProviderFnName as any
    ] as unknown as () => Promise<string>;
    if (typeof accessTokenProvider !== "function") {
      throw new Error("access-token-provider attribute is not a function");
    }

    let accessTokenRefreshInterval: any = this.getAttribute(
      "access-token-refresh-interval",
    );
    if (accessTokenRefreshInterval) {
      accessTokenRefreshInterval = parseInt(accessTokenRefreshInterval, 10);
    } else {
      accessTokenRefreshInterval = 5 * 60 * 1000;
    }

    const lang = this.getAttribute("lang") || "en";
    const baseURL = this.getAttribute("base-url");

    /*
     * Set base URL
     */
    if (baseURL) {
      setBaseURL(baseURL);
      window.auditizeBaseURL = baseURL;
    }

    const root = ReactDOM.createRoot(this.shadowRoot as ShadowRoot);
    root.render(
      <div id="webco" data-mantine-color-scheme="light">
        <style>{mantineCss}</style>
        <style>{mantineDateCss}</style>
        <style>{datatableCss}</style>
        <style>{layersCss}</style>
        <style>{webComponentCss}</style>
        <style>{rsuiteCss}</style>
        <QueryClientProvider client={auditizeQueryClient()}>
          <MantineProvider
            theme={theme}
            defaultColorScheme="light"
            cssVariablesSelector="#webco"
            deduplicateCssVariables={false}
            getRootElement={() => document.getElementById("webco")!}
          >
            <I18nProvider lang={lang}>
              <LogNavigationStateProvider.ForWebComponent repoId={repoId}>
                <AccessTokenAuthProvider
                  accessTokenProvider={accessTokenProvider}
                  refreshInterval={accessTokenRefreshInterval}
                >
                  <Logs withRepoSearchParam={false} withLogFilters={false} />
                </AccessTokenAuthProvider>
              </LogNavigationStateProvider.ForWebComponent>
            </I18nProvider>
          </MantineProvider>
        </QueryClientProvider>
      </div>,
    );
  }
}

customElements.define("auditize-logs", LogWebComponent);
