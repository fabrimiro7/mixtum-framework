import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient, HttpParams } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Ticket, TicketListParams, TicketListResponse } from 'src/app/models/ticket';
import { Task } from 'src/app/models/task';

@Injectable()
export class TicketApiService {

  baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;

    /**
     *  HTTP Headers for API Calls
     */
    private headersForFile: HttpHeaders;
    private headers: HttpHeaders;
    private headersDefault: HttpHeaders;

    constructor(
        private http: HttpClient,
        private cookieService: CookieService,
      ) {
        
        let csfr = this.cookieService.get('csrftoken');
        if (typeof(csfr) === 'undefined') {
          csfr = '';
        }
    
        this.headers = new HttpHeaders()
          .set('content-type', 'application/json')
          .set('X-CSRFToken', csfr);
    
        this.headersForFile = new HttpHeaders()
          .set('X-CSRFToken', csfr);
    
        this.headersDefault = new HttpHeaders()
          .set('content-type', 'application/json')
      }

  
  ticketList(params: TicketListParams = {}): Observable<TicketListResponse> {
    const url = `${this.baseUrl}/api/ticket_manager/tickets/`;
    let httpParams = new HttpParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        httpParams = httpParams.set(k, String(v));
      }
    });
    return this.http.get<TicketListResponse>(url, { headers: this.headers, params: httpParams });
  }

  assignedTicketList(): Observable <any> {
    const url: string = this.baseUrl + '/api/ticket_manager/my-assigned-tickets/';
    return this.http.get(url, {headers: this.headers});
  }

  userTicketList(): Observable <any> {
    const url: string = this.baseUrl + '/api/ticket_manager/my-client-tickets/';
    return this.http.get(url, {headers: this.headers});
  }

  addTicket(newTicket: any): Observable <any> {
    const url: string = this.baseUrl + '/api/ticket_manager/tickets-add/';
    return this.http.post(url, newTicket, {headers: this.headers});
  } 

  ticketAll(): Observable <any> {
    const url: string= this.baseUrl + '/api/ticket_manager/tickets-all/';
    return this.http.get(url, {headers: this.headers});
  }

  ticketDetails(idTicket: any): Observable <any> {
    const url: string = this.baseUrl + '/api/ticket_manager/tickets/' + idTicket + '/';
    return this.http.get(url, {headers: this.headers});
  }

  editTicket(idTicket: any, ticket: any): Observable<any> {
    const url: string = this.baseUrl + '/api/ticket_manager/tickets-put/' + idTicket + '/';
    return this.http.put(url, ticket, {headers: this.headers});
  }

  deleteTicket(idTicket: any): Observable<any> {
    const url: string = this.baseUrl + '/api/ticket_manager/tickets/' + idTicket + '/';
    return this.http.delete(url, {headers: this.headers});
  }

  loadMessagesOfTicket(idTicket: any): Observable <any> {
    const url: string = this.baseUrl + '/api/ticket_manager/tickets/' + idTicket + '/messages/';
    return this.http.get(url, {headers: this.headers});
  }

  addMessagesOfTicket(idTicket: any, message: any): Observable <any> {
    
    const url: string = this.baseUrl + '/api/ticket_manager/tickets/' + idTicket + '/messages/';
    return this.http.post(url, message, {headers: this.headers});
  }

  uploadAttachmentTicket(idTicket: any, file: any): Observable <any> {
    const url: string = this.baseUrl + '/api/ticket_manager/attachment-tickets/' + idTicket + '/';
    return this.http.post(url, file, {headers: this.headersForFile});
  }

  uploadAttachmentMessage(idMessage: any, file: any): Observable <any> {
    const url: string = this.baseUrl + '/api/ticket_manager/attachment-message/' + idMessage + '/';
    return this.http.post(url, file, {headers: this.headersForFile});
  }

  getProjectTicketStats(projectId: number, params: any) {
    return this.http.get(`${this.baseUrl}/api/ticket_manager/monthly-tickets/${projectId}/`, { params });
  }

  // Lista ticket con filtri
  listTickets(params: {
    project: number;
    from?: string;
    to?: string;
    ordering?: string;   
    page?: number;
    page_size?: number;
  }) {
    return this.http.get(`${this.baseUrl}/api/tickets/`, { params });
  }

  togglePaymentStatus(ticketID: number): Observable<any> {
    const url = `${this.baseUrl}/api/ticket_manager/ticket-payments-toggle/${ticketID}/`; // adegua se il tuo detail è divers
    return this.http.get<any>(url, { headers: this.headers });
  }

  getProjectTasks(projectId: number): Observable<Task[]> {
    const url = `${this.baseUrl}/api/ticket_manager/tasks/`;
    const params = new HttpParams().set('project', String(projectId));
    return this.http.get<{ data: Task[] }>(url, { headers: this.headers, params })
      .pipe(map(response => Array.isArray(response?.data) ? response.data : []));
  }

  updateTask(taskId: number, payload: Partial<Task>): Observable<Task> {
    const url = `${this.baseUrl}/api/ticket_manager/tasks/${taskId}/`;
    return this.http.patch<Task>(url, payload, { headers: this.headers });
  }

  createTask(projectId: number, payload: Partial<Task>): Observable<Task> {
    const url = `${this.baseUrl}/api/ticket_manager/tasks/`;
    const body = { ...payload, project: projectId };
    return this.http.post<Task>(url, body, { headers: this.headers });
  }

  markTicketAsRead(ticketId: number): Observable<any> {
    const url = `${this.baseUrl}/api/ticket_manager/tickets/${ticketId}/mark-as-read/`;
    return this.http.post(url, {}, { headers: this.headers });
  }
}
