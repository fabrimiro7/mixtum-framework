import { User } from './user';

export interface Phase {
  id: number;
  title: string;
  description: string;
  status: string;
  status_display?: string;
  priority: string;
  priority_display?: string;
  owner: User | null;
  start_date?: string | null;
  due_date?: string | null;
  project_id: number;
  created_at?: string;
  updated_at?: string;
  project?: {
    id: number;
    title: string;
  };
}
