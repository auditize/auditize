import { createContext, useContext, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { deserializeDate } from "@/utils/date";
import { addQueryParamToLocation } from "@/utils/router";

import {
  buildLogSearchParams,
  LogSearchParams,
  logSearchParamsToURLSearchParams,
  prepareLogSearchParamsForApi,
} from "./api";

type LogContextProps = {
  displayedLogId: string | null;
  setDisplayedLogId: (id: string | null) => void;
  filter: LogSearchParams;
  setFilter: (filter: LogSearchParams) => void;
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
  const [filter, setFilter] = useState<LogSearchParams>({
    ...buildLogSearchParams(),
    repoId,
  });

  return (
    <StateLogContext.Provider
      value={{
        displayedLogId,
        setDisplayedLogId,
        filter,
        setFilter,
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

function searchParamsToFilter(params: URLSearchParams): LogSearchParams {
  // filter the params from the LogsFilterParams available keys (white list)
  // in order to avoid possible undesired keys in LogsFilterParams resulting object
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
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  const setDisplayedLogId = (logId: string | null) => {
    if (logId === null) {
      navigate(-1);
    } else {
      navigate(addQueryParamToLocation(location, "log", logId));
    }
  };

  const displayedLogId = searchParams.get("log") || null;

  const filter = searchParamsToFilter(searchParams);

  const setFilter = (newFilter: LogSearchParams) => {
    // Do not keep the "repo auto-select redirect" in the history,
    // so the user can still go back to the previous page
    const isAutoSelectRepo = !!(!filter.repoId && newFilter.repoId);
    setSearchParams(logSearchParamsToURLSearchParams(newFilter), {
      replace: isAutoSelectRepo,
    });
  };

  return (
    <StateLogContext.Provider
      value={{
        displayedLogId,
        setDisplayedLogId,
        filter,
        setFilter,
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
