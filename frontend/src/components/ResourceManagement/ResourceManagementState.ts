import { useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { addQueryParamToLocation } from "@/utils/router";

interface ResourceManagementState {
  // Page
  page: number;
  setPage: (page: number) => void;

  // New resource edition
  isNew: boolean;
  setIsNew: (isNew: boolean) => void;

  // Existing resource edition
  resourceId: string | null;
  setResourceId: (id: string | null) => void;
  resourceLink?: (id: string) => string;

  // Search
  search: string;
  setSearch: (search: string) => void;
}

function useResourceManagementStateWithURL(): ResourceManagementState {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();

  // Page
  const page = params.has("page") ? parseInt(params.get("page") || "") : 1;
  const setPage = (value: number) =>
    navigate(addQueryParamToLocation(location, "page", value.toString()));

  // New resource edition
  const isNew = params.has("new");
  const setIsNew = (value: boolean) => {
    if (value) {
      navigate(addQueryParamToLocation(location, "new"));
    } else {
      navigate(-1);
    }
  };

  // Existing resource edition
  const resourceId = params.get("id");
  const setResourceId = (id: string | null) => {
    if (id) {
      throw new Error("Operation not supported, use resourceLink instead");
    } else {
      navigate(-1);
    }
  };
  const resourceLink = (id: string) =>
    addQueryParamToLocation(location, "id", id);

  // Search
  const search = params.get("q") || "";
  const setSearch = (value: string) => setParams({ q: value });

  return {
    page,
    setPage,
    isNew,
    setIsNew,
    resourceId,
    setResourceId,
    resourceLink,
    search,
    setSearch,
  };
}

function useResourceManagementStateWithUseState(): ResourceManagementState {
  // Page
  const [page, setPage] = useState(1);

  // New resource edition
  const [isNew, setIsNew] = useState(false);

  // Existing resource edition
  const [resourceId, setResourceId] = useState<string | null>(null);
  const resourceLink = undefined;

  // Search
  const [search, setSearch] = useState("");

  return {
    page,
    setPage,
    isNew,
    setIsNew,
    resourceId,
    setResourceId,
    resourceLink,
    search,
    setSearch,
  };
}

export function useResourceManagementState(
  mode: "url" | "useState",
): ResourceManagementState {
  if (mode === "useState") {
    return useResourceManagementStateWithUseState();
  } else {
    return useResourceManagementStateWithURL();
  }
}
