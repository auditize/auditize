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
