type Log = {
  id: number;
  saved_at: string;
  event: {
    name: string;
    category: string;
  };
  actor?: {
    type: string;
    id: string;
    name: string;
  };
  resource?: {
    type: string;
    id: string;
    name: string;
  };
  node_path: {
    id: string;
    name: string;
  }[];
};

type LogListResponse = {
  data: Log[];
  pagination: {
    next_cursor: string | null;
  }
};
