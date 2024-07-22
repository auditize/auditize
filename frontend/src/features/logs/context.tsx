import { useLocalStorage } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { deserializeDate } from "@/utils/date";
import { addQueryParamToLocation } from "@/utils/router";

import {
  getLogFilter,
  normalizeFilterColumnsForApi,
  unnormalizeFilterColumnsFromApi,
} from "../logfilters";
import { useLogFilterMutation } from "../logfilters/api";
import {
  buildLogSearchParams,
  LogSearchParams,
  logSearchParamsToURLSearchParams,
} from "./api";
import {
  DEFAULT_COLUMNS,
  useLogRepoQuery,
  useLogSelectedColumns,
} from "./hooks";

type LogContextProps = {
  displayedLogId: string | null;
  setDisplayedLogId: (id: string | null) => void;
  searchParams: LogSearchParams;
  setSearchParams: (params: LogSearchParams) => void;
  selectedColumns: string[];
  setSelectedColumns: (columns: string[] | null) => void;
  filterId?: string;
};

const StateLogContext = createContext<LogContextProps | null>(null);

export function StateLogContextProvider({
  repoId,
  children,
}: {
  repoId: string;
  children: React.ReactNode;
}) {
  const [displayedLogId, setDisplayedLogId] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useState<LogSearchParams>({
    ...buildLogSearchParams(),
    repoId,
  });
  const [selectedColumns, setSelectedColumns] = useLogSelectedColumns(repoId);

  return (
    <StateLogContext.Provider
      value={{
        displayedLogId,
        setDisplayedLogId,
        searchParams,
        setSearchParams,
        selectedColumns,
        setSelectedColumns,
      }}
    >
      {children}
    </StateLogContext.Provider>
  );
}

function unflattensCustomFields(
  params: Record<string, string>,
  prefix: string,
): Map<string, string> {
  const customFields = new Map<string, string>();
  for (const [name, value] of Object.entries(params)) {
    const parts = name.split(".");
    if (parts.length === 2 && parts[0] === prefix) {
      customFields.set(parts[1], value);
    }
  }
  return customFields;
}

function unflattensLogSearchParameters(
  params: Record<string, string>,
): LogSearchParams {
  // filter the params from the LogSearchParams available keys (white list)
  // in order to avoid possible undesired keys in LogSearchParams resulting object
  const template = buildLogSearchParams();
  const obj = Object.fromEntries(
    Object.keys(template).map((key) => [key, params[key] ?? ""]),
  );
  return {
    ...obj,
    since: obj.since ? deserializeDate(obj.since) : null,
    until: obj.until ? deserializeDate(obj.until) : null,
    actorExtra: unflattensCustomFields(params, "actor"),
    resourceExtra: unflattensCustomFields(params, "resource"),
    source: unflattensCustomFields(params, "source"),
    details: unflattensCustomFields(params, "details"),
  } as LogSearchParams;
}

const UrlLogContext = createContext<LogContextProps | null>(null);

export function UrlLogContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { t } = useTranslation();
  const [urlSearchParams, setUrlSearchParams] = useSearchParams();
  const filterId = urlSearchParams.get("filterId");
  const location = useLocation();
  const navigate = useNavigate();
  const repoQuery = useLogRepoQuery();
  const [defaultRepo, setDefaultRepo] = useLocalStorage({
    key: "auditize-default-repo",
    getInitialValueInEffect: false,
  });
  const [repoSelectedColumns, setRepoSelectedColumns] = useLogSelectedColumns(
    urlSearchParams.get("repoId") || "",
  );
  const filterQuery = useQuery({
    queryKey: ["logFilter", filterId],
    queryFn: () => getLogFilter(filterId!),
    enabled: !!filterId,
  });
  const filterMutation = useLogFilterMutation(filterId!, {
    onError: () =>
      notifications.show({
        title: t("common.errorModalTitle"),
        message: t("log.filter.updateError"),
        color: "red",
        autoClose: false,
      }),
  });

  const setDisplayedLogId = (logId: string | null) => {
    if (logId === null) {
      navigate(-1);
    } else {
      navigate(addQueryParamToLocation(location, "log", logId));
    }
  };

  const displayedLogId = urlSearchParams.get("log") || null;

  // Build log search parameters from URL search parameters or filterId (if provided)
  // In case both are provided, the URL search parameters have precedence
  let logSearchParams: LogSearchParams;
  if (!urlSearchParams.has("repoId") && filterId && filterQuery.data) {
    logSearchParams = {
      ...unflattensLogSearchParameters(filterQuery.data.searchParams),
      repoId: filterQuery.data.repoId,
    };
  } else {
    logSearchParams = unflattensLogSearchParameters(
      Object.fromEntries(urlSearchParams.entries()),
    );
  }

  const setLogSearchParams = (newLogSearchParams: LogSearchParams) => {
    // Do not keep the "repo auto-select redirect" in the history,
    // so the user can still go back to the previous page
    const isAutoSelectRepo = !!(
      !logSearchParams.repoId && newLogSearchParams.repoId
    );

    const newUrlSearchParams =
      logSearchParamsToURLSearchParams(newLogSearchParams);
    if (filterId) {
      newUrlSearchParams.set("filterId", filterId);
    }
    setUrlSearchParams(newUrlSearchParams, {
      replace: isAutoSelectRepo,
    });
  };

  let selectedColumns: string[];
  let setSelectedColumns: (columns: string[] | null) => void;
  if (filterId && filterQuery.data) {
    selectedColumns = unnormalizeFilterColumnsFromApi(filterQuery.data.columns);
    setSelectedColumns = (columns: string[] | null) =>
      filterMutation.mutate({
        columns: normalizeFilterColumnsForApi(columns ?? DEFAULT_COLUMNS),
      });
  } else {
    selectedColumns = repoSelectedColumns;
    setSelectedColumns = setRepoSelectedColumns;
  }

  // Auto-select repository if the repoId is not in the URL
  useEffect(() => {
    if (!filterId && !logSearchParams.repoId && repoQuery.data) {
      // repo has not been auto-selected yet
      const repos = repoQuery.data;

      // if no default repo or default repo is not in the list, select the first one (if any)
      if (!defaultRepo || !repos.find((repo) => repo.id === defaultRepo)) {
        if (repos.length > 0) {
          setLogSearchParams({ ...logSearchParams, repoId: repos[0].id });
        }
      } else {
        // otherwise, select the default/previously selected repo (local storage)
        setLogSearchParams({ ...logSearchParams, repoId: defaultRepo });
      }
    }
  });

  // Update auditize-default-repo local storage key on repoId change
  // so that the repo selector will be automatically set to the last selected repo
  // when the page is loaded without a repoId in the URL
  useEffect(() => {
    if (logSearchParams.repoId) {
      setDefaultRepo(logSearchParams.repoId);
    }
  }, [logSearchParams.repoId]);

  return (
    <StateLogContext.Provider
      value={{
        displayedLogId,
        setDisplayedLogId,
        searchParams: logSearchParams,
        setSearchParams: setLogSearchParams,
        selectedColumns,
        setSelectedColumns,
        filterId: filterId ?? undefined,
      }}
    >
      {children}
    </StateLogContext.Provider>
  );
}

export function useLogContext(): LogContextProps {
  const stateLogContext = useContext(StateLogContext);
  const urlLogContext = useContext(UrlLogContext);

  if (!stateLogContext && !urlLogContext) {
    throw new Error(
      "useLogState must be used within a LogStateContextProvider or UrlLogContextProvider",
    );
  }
  return stateLogContext || urlLogContext!;
}
