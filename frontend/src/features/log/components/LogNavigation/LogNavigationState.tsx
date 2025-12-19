import { useLocalStorage } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { notifyError } from "@/components/notifications";
import {
  getLogFilter,
  normalizeFilterColumnsForApi,
  unnormalizeFilterColumnsFromApi,
  useLogFilterMutation,
} from "@/features/log-filter";
import { LogFilter } from "@/features/log-filter/api";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { useLogRepoListQuery } from "@/features/repo";
import { addQueryParamToLocation } from "@/utils/router";

type LogContextProps = {
  displayedLogId: string | null;
  setDisplayedLogId: (id: string | null) => void;
  searchParams: LogSearchParams;
  setSearchParams: (params: LogSearchParams) => void;
  selectedColumns: string[];
  setSelectedColumns: (columns: string[] | null) => void;
  filter?: LogFilter;
  isFilterDirty?: boolean;
  logComponentRef: React.RefObject<HTMLDivElement>;
};

const StateLogContext = createContext<LogContextProps | null>(null);

const DEFAULT_SELECTED_COLUMNS = [
  "emittedAt",
  "actor",
  "action",
  "resource",
  "entity",
  "tag",
];

function useLogSelectedColumns(
  repoId: string,
): [string[], (columns: string[] | null) => void] {
  const [perRepoColumns, setPerRepoColumns] = useLocalStorage<
    Record<string, string[]>
  >({
    key: `auditize-log-columns`,
    defaultValue: {},
  });

  // In 0.10.0, the emittedAt date has been added alongside the savedAt date,
  // but the UI only shows one date: the emittedAt.
  // We need to handle this case by removing the savedAt column and adding
  // the emittedAt column if it is not already present.
  let columns = perRepoColumns[repoId] ?? DEFAULT_SELECTED_COLUMNS;
  if (columns.includes("savedAt")) {
    columns = columns.filter((column) => column !== "savedAt");
    if (!columns.includes("emittedAt")) {
      columns = [...columns, "emittedAt"];
    }
  }

  return [
    columns,
    (newColumns) => {
      setPerRepoColumns((perRepoColumns) => ({
        ...perRepoColumns,
        [repoId]: newColumns ? newColumns : DEFAULT_SELECTED_COLUMNS,
      }));
    },
  ];
}

const UrlLogContext = createContext<LogContextProps | null>(null);

// Build log search parameters from URL search parameters or log filter (if provided).
// In case both are provided, the URL search parameters have precedence.
function useLogSearchParams(
  urlSearchParams: URLSearchParams,
  logFilter: LogFilter | undefined,
): LogSearchParams {
  // Use "useMemo" to avoid re-creating a new LogSearchParams object on every render
  return useMemo(
    () =>
      !urlSearchParams.has("repoId") && logFilter
        ? LogSearchParams.deserialize({
            ...logFilter.searchParams,
            repoId: logFilter.repoId,
          })
        : LogSearchParams.deserialize(
            Object.fromEntries(urlSearchParams.entries()),
          ),
    [urlSearchParams, logFilter],
  );
}

export function LogNavigationStateProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { t } = useTranslation();
  const logComponentRef = useRef<HTMLDivElement>(null);
  const [urlSearchParams, setUrlSearchParams] = useSearchParams();
  const filterId = urlSearchParams.get("filterId");
  const location = useLocation();
  const navigate = useNavigate();
  const repoListQuery = useLogRepoListQuery();
  const [defaultRepo, setDefaultRepo] = useLocalStorage({
    key: "auditize-default-repo",
    getInitialValueInEffect: false,
  });
  const [repoSelectedColumns, setRepoSelectedColumns] = useLogSelectedColumns(
    urlSearchParams.get("repoId") || "",
  );
  const filterQuery = useQuery({
    queryKey: ["logFilters", filterId],
    queryFn: () => getLogFilter(filterId!),
    enabled: !!filterId,
  });
  const filterMutation = useLogFilterMutation(filterId!, {
    onError: () => notifyError(t("log.filter.updateError")),
  });
  const logSearchParams = useLogSearchParams(urlSearchParams, filterQuery.data);

  const setDisplayedLogId = (logId: string | null) => {
    if (logId === null) {
      navigate(-1);
    } else {
      navigate(addQueryParamToLocation(location, "log", logId));
    }
  };

  const displayedLogId = urlSearchParams.get("log") || null;

  const setLogSearchParams = (newLogSearchParams: LogSearchParams) => {
    // Do not keep the "repo auto-select redirect" in the history,
    // so the user can still go back to the previous page
    const isAutoSelectRepo = !!(
      !logSearchParams.repoId && newLogSearchParams.repoId
    );

    const newUrlSearchParams = new URLSearchParams(
      newLogSearchParams.serialize(),
    );
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
        columns: normalizeFilterColumnsForApi(
          columns ?? DEFAULT_SELECTED_COLUMNS,
        ),
      });
  } else {
    selectedColumns = repoSelectedColumns;
    setSelectedColumns = setRepoSelectedColumns;
  }

  // Auto-select repository if the repoId is not in the URL
  useEffect(() => {
    if (!filterId && !logSearchParams.repoId && repoListQuery.data) {
      // repo has not been auto-selected yet
      const repos = repoListQuery.data;

      // if no default repo or default repo is not in the list, select the first one (if any)
      if (!defaultRepo || !repos.find((repo) => repo.id === defaultRepo)) {
        if (repos.length > 0) {
          setLogSearchParams(
            LogSearchParams.fromProperties({
              ...logSearchParams,
              repoId: repos[0].id,
            }),
          );
        }
      } else {
        // otherwise, select the default/previously selected repo (local storage)
        setLogSearchParams(
          LogSearchParams.fromProperties({
            ...logSearchParams,
            repoId: defaultRepo,
          }),
        );
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
        filter: filterQuery.data,
        isFilterDirty: filterQuery.data
          ? urlSearchParams.has("repoId")
          : undefined,
        logComponentRef,
      }}
    >
      {children}
    </StateLogContext.Provider>
  );
}

function LogNavigationForWebComponentStateProvider({
  repoId,
  children,
}: {
  repoId: string;
  children: React.ReactNode;
}) {
  const logComponentRef = useRef<HTMLDivElement>(null);
  const [displayedLogId, setDisplayedLogId] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useState<LogSearchParams>(
    LogSearchParams.fromProperties({ repoId }),
  );
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
        logComponentRef,
      }}
    >
      {children}
    </StateLogContext.Provider>
  );
}

LogNavigationStateProvider.ForWebComponent =
  LogNavigationForWebComponentStateProvider;

export function useLogNavigationState(): LogContextProps {
  const stateLogContext = useContext(StateLogContext);
  const urlLogContext = useContext(UrlLogContext);

  if (!stateLogContext && !urlLogContext) {
    throw new Error(
      "useLogState must be used within a LogStateContextProvider or UrlLogContextProvider",
    );
  }
  return stateLogContext || urlLogContext!;
}
