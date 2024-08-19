import { MantineProvider } from "@mantine/core";
import mantineCss from "@mantine/core/styles.layer.css?inline";
import mantineDateCss from "@mantine/dates/styles.layer.css?inline";
import { QueryClientProvider } from "@tanstack/react-query";
import datatableCss from "mantine-datatable/styles.layer.css?inline";
import ReactDOM from "react-dom/client";
import rsuiteCss from "rsuite/dist/rsuite-no-reset.min.css?inline";

import { theme } from "@/theme";

import { LogNavigationStateProvider, Logs } from "./features/log";
import { I18nProvider } from "./i18n";
import layersCss from "./layers.css?inline";
import { enableAccessTokenAuthentication, setBaseURL } from "./utils/axios";
import { auditizeQueryClient } from "./utils/query";
import webComponentCss from "./web-component.css?inline";

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

    const accessToken = this.getAttribute("access-token");
    if (!accessToken) {
      throw new Error("access-token attribute is missing");
    }
    const accessTokenRefreshFnName = this.getAttribute("access-token-refresh");
    if (!accessTokenRefreshFnName) {
      throw new Error("access-token-refresh attribute is missing");
    }
    const accessTokenRefreshFn = window[
      accessTokenRefreshFnName as any
    ] as unknown as () => Promise<string>;
    if (typeof accessTokenRefreshFn !== "function") {
      throw new Error("access-token-refresh attribute is not a function");
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
     * Set authentication
     */
    enableAccessTokenAuthentication(accessToken);
    setInterval(() => {
      accessTokenRefreshFn().then((newAccessToken) => {
        enableAccessTokenAuthentication(newAccessToken);
      });
    }, accessTokenRefreshInterval);

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
                <Logs withRepoSearchParam={false} withLogFilters={false} />
              </LogNavigationStateProvider.ForWebComponent>
            </I18nProvider>
          </MantineProvider>
        </QueryClientProvider>
      </div>,
    );
  }
}

customElements.define("auditize-logs", LogWebComponent);
