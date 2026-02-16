// ticket-list.component.ts
import { Component, OnInit, ViewChild } from '@angular/core';
import { catchError, of } from 'rxjs';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';
import { MatSort, Sort } from '@angular/material/sort';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { AuthService } from 'src/app/services/auth/auth.service';
import { DateParser } from 'src/app/util/date_parse';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { Ticket } from 'src/app/models/ticket';

@Component({
  selector: 'app-ticket-list-admin',
  templateUrl: './ticket-list-admin.component.html',
  styleUrls: ['./ticket-list-admin.component.css']
})
export class TicketListAdminComponent implements OnInit {

  userType: string = '';
  tickets: Ticket[] = [];
  currentUserId: number | null = null;

  // paging + sorting server-side
  total = 0;
  pageIndex = 0;           // MatPaginator è 0-based
  pageSize = 50;
  pageSizeOptions = [50, 100, 200];

  sortActive: string = 'opening_date';
  sortDirection: 'asc' | 'desc' = 'desc'; // es.: più recenti prima

  // filtri “attivi” da mandare al server
  filterStatus: string | undefined;
  filterPriority: string | undefined;
  filterProject: number | undefined;
  searchText: string | undefined;

  displayedAdminColumns: string[] = ['id', 'title', 'awaiting_response', 'client', 'status', 'priority', 'assignee', 'date', 'action'];
  displayedClientColumns: string[] = ['id', 'title', 'awaiting_response', 'client', 'status', 'assignee', 'date', 'action'];


  SuperAdminFilter = [
    { name: 'Tutti', key: undefined, isActive: true },
    { name: 'Da assegnare', key: 'da_assegnare', isActive: false},
    { name: 'Assegnati', key: 'assegnati', isActive: false},
    { name: 'Chiusi', key: 'closed_group', isActive: false}
  ];
  AdminFilter = [
    { name: 'Tutti', key: undefined, isActive: true },
    { name: 'Attivi', key: 'active', isActive: false},
    { name: 'Chiusi', key: 'closed_group', isActive: false}
  ];
  UserFilter = [
    { name: 'Tutti', key: undefined, isActive: true },
    { name: 'Aperti', key: 'open', isActive: false },
    { name: 'In attesa', key: 'in_progress', isActive: false},
    { name: 'Chiusi', key: 'closed_group', isActive: false}
  ];

  constructor(
    private apiTicket: TicketApiService,
    private router: Router,
    private perm: PermissionService,
    private cookieService: CookieService,
    private route: ActivatedRoute,
    private dataParser: DateParser,
    private jwt: JWTUtils,
    private auth: AuthService,
  ) {}

  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatPaginator) paginator!: MatPaginator;

ngOnInit(): void {
  const token = this.cookieService.get('token');
  this.userType = this.perm.checkPermission(token);
  this.currentUserId = this.jwt.getUserIDFromJWT();

  // Legge i query params e ripristina stato UI
  this.route.queryParamMap.subscribe(qp => {
    // filtro chip
    const filter = qp.get('filter') || undefined;
    this.filterStatus = filter;

    // pagina e page size (DRF è 1-based; MatPaginator è 0-based)
    const qPage = Number(qp.get('page'));
    this.pageIndex = isNaN(qPage) || qPage < 1 ? 0 : qPage - 1;

    const qPageSize = Number(qp.get('page_size'));
    this.pageSize = !isNaN(qPageSize) && qPageSize > 0 ? qPageSize : this.pageSize;

    // ordering (-field/field)
    const qOrdering = qp.get('ordering');
    if (qOrdering) {
      this.sortDirection = qOrdering.startsWith('-') ? 'desc' : 'asc';
      this.sortActive = qOrdering.replace(/^-/, '') || this.sortActive;
    }

    // eventuali altri filtri (opzionali)
    this.filterPriority = qp.get('priority') ?? this.filterPriority;
    const proj = qp.get('project');
    this.filterProject = proj ? Number(proj) : this.filterProject;
    this.searchText = qp.get('search') ?? this.searchText;

    // evidenzia la chip corretta
    this.syncActiveChipFromKey(this.filterStatus);

    // carica dati coerenti con l’URL
    this.loadTickets();
  });
}

  private syncActiveChipFromKey(key: string | undefined) {
    const list = this.userType === 'Admin' ? this.AdminFilter
              : this.userType === 'Utente' ? this.UserFilter
              : this.SuperAdminFilter;

    list.forEach(f => f.isActive = (f.key === key || (!key && f.key === undefined)));
  }
  // ---- SERVER CALL ----
  private loadTickets(): void {
    const ordering = this.sortActive ? (this.sortDirection === 'desc' ? `-${this.sortActive}` : this.sortActive) : undefined;

    const params: any = {
      page: this.pageIndex + 1,       
      page_size: this.pageSize,
      ordering,
    };

    if (this.filterStatus && !['closed_group', 'active', 'assegnati', 'da_assegnare'].includes(this.filterStatus)) {
      params.status = this.filterStatus;
    }

    if (this.filterStatus === 'closed_group') {
      params.status__in = 'resolved,closed'; 
    } else if (this.filterStatus === 'active') {
      params.status__in = 'open,in_progress';
    } else if (this.filterStatus === 'assegnati') {
      params.assigned = 'true';
    } else if (this.filterStatus === 'da_assegnare') {
      params.assigned = 'false';
    }

    if (this.filterPriority) params.priority = this.filterPriority;
    if (this.filterProject)  params.project  = this.filterProject;
    if (this.searchText)     params.search   = this.searchText;

    this.apiTicket.ticketList(params)
      .pipe(
        catchError(err => {
          console.error('Errore API ticketList', err);
          this.tickets = [];
          this.total = 0;
          return of({ count: 0, data: [] } as any);
        })
      )
      .subscribe(resp => {
        console.log('API ticketList response:', resp);
        this.tickets = resp.results;
        this.total = resp.count;
      });
  }

  onPageChange(e: PageEvent) {
    this.pageIndex = e.pageIndex;
    this.pageSize = e.pageSize;
    this.updateUrlParams(true); // nuova pagina -> ok aggiungere history
    this.loadTickets();
  }

  onSortChange(sort: Sort) {
    this.sortActive = sort.active || 'opening_date';
    this.sortDirection = (sort.direction || 'asc') as 'asc' | 'desc';
    this.pageIndex = 0;
    this.updateUrlParams();
    this.loadTickets();
  }

  selectedFilter(selectedFilter: any) {
    const list = this.userType === 'Admin' ? this.AdminFilter
              : this.userType === 'Utente' ? this.UserFilter
              : this.SuperAdminFilter;

    list.forEach(f => (f.isActive = f === selectedFilter));
    this.filterStatus = selectedFilter.key;
    this.pageIndex = 0;

    this.updateUrlParams();
    this.loadTickets();
  }

  // helpers
  redirectTo(component: string){ this.router.navigate([component]); }
  truncate(text: string, limit: number){ return text.length > limit ? text.substring(0, limit) + '...' : text; }
  trasformDateHours(date: string){ return this.dataParser.ISOToNormalDate(date); }
  trasformDate(date: string){ return date ? this.dataParser.ISOToNormalDateNoTime(date) : '-'; }

  getDisplayedColumns(){
    return this.userType !== 'Utente' ? this.displayedAdminColumns : this.displayedClientColumns;
  }

  getTicketAssignees(assignees: any[]): string {
    if (!assignees || assignees.length === 0) return '-';
    if (assignees.length === 1) return assignees[0].first_name;
    return `${assignees[0].first_name} +${assignees.length - 1}`;
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'open': return 'status-open';
      case 'in_progress': return 'status-in-progress';
      case 'resolved': return 'status-resolved';
      case 'closed': return 'status-closed';
      default: return '';
    }
  }

  getPriorityClass(p: string): string {
    switch (p) {
      case 'low': return 'low-priority';
      case 'medium': return 'medium-priority';
      case 'high': return 'high-priority';
      default: return '';
    }
  }

  private updateUrlParams(pushHistory = false) {
  const ordering = this.sortActive
    ? (this.sortDirection === 'desc' ? `-${this.sortActive}` : this.sortActive)
    : undefined;

  const params: Params = {
    filter: this.filterStatus ?? null,     // null => rimuove il param
    page: this.pageIndex + 1,
    page_size: this.pageSize,
    ordering: ordering ?? null,
    priority: this.filterPriority ?? null,
    project: this.filterProject ?? null,
    search: this.searchText ?? null,
  };

  this.router.navigate([], {
    relativeTo: this.route,
    queryParams: params,
    queryParamsHandling: 'merge',
    replaceUrl: !pushHistory, // evita di “sporcare” la history ad ogni pagina
  });
}

  getFullName(u: any): string {
    if (!u) return '';
    const fn = (u.first_name || '').trim();
    const ln = (u.last_name || '').trim();
    return (fn + ' ' + ln).trim() || u.username || u.email || 'Utente';
  }

  getInitials(u: any): string {
    const fn = (u?.first_name || '').trim();
    const ln = (u?.last_name || '').trim();
    const a = (fn ? fn[0] : '') + (ln ? ln[0] : '');
    return a ? a.toUpperCase() : (u?.username?.[0] || u?.email?.[0] || '?').toUpperCase();
  }

  getAssigneesTooltip(list: any[]): string {
    if (!list?.length) return '';
    return list.map(u => this.getFullName(u)).join(', ');
  }

  // opzionale: mappa ID->nome (se hai i progetti caricati altrove)
  private projectLabels: Record<number, string> = {
    // 1: 'Nome Progetto', // popola se vuoi
  };

  isAwaitingResponse(t: any): boolean {
    if (t?.status === 'resolved') return false;
    const lm = t?.last_message;
    if (!lm?.author) return false;
    const p = lm.author.permission;
    return (p === 50 || p === 100) && lm.author.id !== this.currentUserId;
  }

  getProjectLabel(t: any): string | null {
    // Se l'API in futuro fornisce un oggetto progetto (es. {id, name}), gestiscilo qui
    const p = t?.project;
    if (!p && p !== 0) return null;

    // caso: oggetto con name
    if (typeof p === 'object' && p?.title) return p.title;

    // caso: solo id numerico => prova mapping locale, altrimenti fallback
    if (typeof p === 'number') return this.projectLabels[p] || `Progetto #${p}`;

    return null;
  }
}
