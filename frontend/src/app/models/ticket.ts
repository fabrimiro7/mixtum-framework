import { User } from "./user";

export class Ticket {
    
    constructor(
        public id: number | any,
        public title: string | any,
        public description: string | any,
        public client: number | any,
        public project: number | any,
        public attachments : any[] | any,
        public assignees: User[] | any,
        public priority: string | any,
        public hours_estimation: number | any,
        public opening_date: Date | any,
        public closing_date: Date | any,
        public cost_estimation: number | any,
        public status: string | any,
        public expected_resolution_date: Date | any,
        public expected_action: string | any,
        public real_action: string | any,
        public ticket_linked: Ticket | any,
        public ticket_workspace: number | any,
        public ticket_type: string | any,
        public payments_status: boolean | any,
        public last_message?: { id: number; insert_date: string; author: { id: number; permission: number } } | null,
        public last_read_at?: string | null,
        public has_unread?: boolean,
      ) {}
  }

export interface TicketListParams {
  page?: number;           
  page_size?: number;      
  status?: string;         
  priority?: string;       
  project?: number;        
  project__in?: string;    
  search?: string;        
  ordering?: string;
  year?: number;      
  month?: number;     
  from?: string;      
  to?: string;             
}

export interface TicketListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results?: any[];  
  data?: any[];    
  page?: number;
  page_size?: number;
}