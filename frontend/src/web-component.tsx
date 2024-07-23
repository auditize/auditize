import { MantineProvider } from "@mantine/core";
import mantineCss from "@mantine/core/styles.layer.css?inline";
import { QueryClientProvider } from "@tanstack/react-query";
import datatableCss from "mantine-datatable/styles.layer.css?inline";
import ReactDOM from "react-dom/client";
import rsuiteCss from "rsuite/dist/rsuite-no-reset.min.css?inline";

import { theme } from "@/theme";

import { LogNavigationStateProvider, Logs } from "./features/logs";
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
    const repoId = this.getAttribute("repo-id");
    if (!repoId) {
      throw new Error("repo-id attribute is required");
    }
    const accessToken = this.getAttribute("access-token");
    if (!accessToken) {
      throw new Error("access-token attribute is required");
    }
    const lang = this.getAttribute("lang") || "en";
    const baseURL = this.getAttribute("base-url");

    enableAccessTokenAuthentication(accessToken);

    if (baseURL) {
      setBaseURL(baseURL);
      window.auditizeBaseURL = baseURL;
    }

    const root = ReactDOM.createRoot(this.shadowRoot as ShadowRoot);
    root.render(
      <div id="webco" data-mantine-color-scheme="light">
        <style>{mantineCss}</style>
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
