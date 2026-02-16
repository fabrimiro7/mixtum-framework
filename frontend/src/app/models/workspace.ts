export interface Workspace {
  id: number;
  workspace_name: string;
  workspace_description?: string | null;
  workspace_logo?: string | null;
  users_count?: number;
}
