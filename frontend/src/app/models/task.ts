import { User } from './user';

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: string;
  status_display?: string;
  priority: string;
  priority_display?: string;
  assignee?: User;
  estimate_hours?: number;
  start_date?: string;
  due_date?: string;
  ticket_id?: number;
  project_id?: number;
  created_at?: string;
  updated_at?: string;
}
