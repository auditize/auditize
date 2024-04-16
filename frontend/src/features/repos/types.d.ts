type Repo = {
  id: string;
  name: string;
  created_at: string;
  stats?: {
    first_log_date: string;
    last_log_date: string;
    log_count: number;
    storage_size: number;
  }
};

type RepoUpdate = {
  name?: string;
};