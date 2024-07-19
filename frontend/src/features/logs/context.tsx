import { useLocalStorage } from "@mantine/hooks";
import { createContext, useContext, useEffect, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { deserializeDate } from "@/utils/date";
import { addQueryParamToLocation } from "@/utils/router";

import {
  buildLogSearchParams,
  LogSearchParams,
  logSearchParamsToURLSearchParams,
} from "./api";
import { useLogRepoQuery } from "./hooks";

type LogContextProps = {
  displayedLogId: string | null;
  setDisplayedLogId: (id: string | null) => void;
  searchParams: LogSearchParams;
  setSearchParams: (params: LogSearchParams) => void;
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

  return (
    <StateLogContext.Provider
      value={{
        displayedLogId,
        setDisplayedLogId,
        searchParams,
        setSearchParams,
      }}
    >
      {children}
    </StateLogContext.Provider>
  );
}

function extractCustomFieldsFromURLSearchParams(
  params: URLSearchParams,
  prefix: string,
): Map<string, string> {
  const customFields = new Map<string, string>();
  for (const [name, value] of params.entries()) {
    const parts = name.split(".");
    if (parts.length === 2 && parts[0] === prefix) {
      customFields.set(parts[1], value);
    }
  }
  return customFields;
}

function urlSearchParamsToLogSearchParams(
  params: URLSearchParams,
): LogSearchParams {
  // filter the params from the LogSearchParams available keys (white list)
  // in order to avoid possible undesired keys in LogSearchParams resulting object
  const template = buildLogSearchParams();
  const obj = Object.fromEntries(
    Object.keys(template).map((key) => [key, params.get(key) || ""]),
  );
  return {
    ...obj,
    since: obj.since ? deserializeDate(obj.since) : null,
    until: obj.until ? deserializeDate(obj.until) : null,
    actorExtra: extractCustomFieldsFromURLSearchParams(params, "actor"),
    resourceExtra: extractCustomFieldsFromURLSearchParams(params, "resource"),
    source: extractCustomFieldsFromURLSearchParams(params, "source"),
    details: extractCustomFieldsFromURLSearchParams(params, "details"),
  } as LogSearchParams;
}

const UrlLogContext = createContext<LogContextProps | null>(null);

export function UrlLogContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [urlSearchParams, setUrlSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const repoQuery = useLogRepoQuery();
  const [defaultRepo, setDefaultRepo] = useLocalStorage({
    key: "auditize-default-repo",
    getInitialValueInEffect: false,
  });

  const setDisplayedLogId = (logId: string | null) => {
    if (logId === null) {
      navigate(-1);
    } else {
      navigate(addQueryParamToLocation(location, "log", logId));
    }
  };

  const displayedLogId = urlSearchParams.get("log") || null;

  const logSearchParams = urlSearchParamsToLogSearchParams(urlSearchParams);

  const setLogSearchParams = (newLogSearchParams: LogSearchParams) => {
    // Do not keep the "repo auto-select redirect" in the history,
    // so the user can still go back to the previous page
    const isAutoSelectRepo = !!(
      !logSearchParams.repoId && newLogSearchParams.repoId
    );
    setUrlSearchParams(logSearchParamsToURLSearchParams(newLogSearchParams), {
      replace: isAutoSelectRepo,
    });
  };

  useEffect(() => {
    if (!logSearchParams.repoId && repoQuery.data) {
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
  }, [repoQuery.data]);

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
