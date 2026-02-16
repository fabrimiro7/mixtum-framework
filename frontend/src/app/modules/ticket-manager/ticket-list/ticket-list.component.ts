// ticket-list.component.ts

import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { MatSort, Sort } from '@angular/material/sort';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { catchError, of } from 'rxjs';

import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';
import { AuthService } from 'src/app/services/auth/auth.service';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { DateParser } from 'src/app/util/date_parse';
import { Ticket } from 'src/app/models/ticket';

@Component({
  selector: 'app-ticket-list',
  templateUrl: './ticket-list.component.html',
  styleUrls: ['./ticket-list.component.css']
})
export class TicketListComponent implements OnInit {

  userType: string = '';
  tickets: Ticket[] = [];
  canAccessManagement = false;
  currentUserId: number | null = null;

  // Tab principali: Tutti / Miei / Del workspace
  mainFilter: 'all' | 'mine' | 'workspace' = 'all';
  statusFilter: 'open' | 'in_progress' | 'resolved' | undefined = undefined;

  mainFilters: Array<{ key: 'all' | 'mine' | 'workspace'; label: string }> = [
    { key: 'all', label: 'Tutti' },
    { key: 'mine', label: 'Miei' },
    { key: 'workspace', label: 'Del workspace' },
  ];
  statusFilters: Array<{ key: 'open' | 'in_progress' | 'resolved'; label: string }> = [
    { key: 'open', label: 'Aperti' },
    { key: 'in_progress', label: 'In corso' },
    { key: 'resolved', label: 'Risolti' },
  ];

  projectList: { id: number; title: string }[] = [];
  selectedProjectIds: number[] = [];
  compareProjectIds = (a: number, b: number): boolean => a === b;

  // paging + sorting
  total = 0;
  pageIndex = 0;
  pageSize = 50;
  pageSizeOptions = [50, 100, 200];

  // default sort → per tab "miei"
  sortActive: string = 'priority_custom';
  sortDirection: 'asc' | 'desc' = 'asc';

  displayedAdminColumns: string[] = [
    'id', 'title', 'awaiting_response', 'client', 'status', 'priority', 'assignee', 'date', 'action'
  ];
  displayedClientColumns: string[] = [
    'id', 'title', 'awaiting_response', 'status', 'priority', 'assignee', 'date', 'action'
  ];

  constructor(
    private apiTicket: TicketApiService,
    private apiProject: ProjectApiService,
    private router: Router,
    private route: ActivatedRoute,
    private perm: PermissionService,
    private cookieService: CookieService,
    private dataParser: DateParser,
    private auth: AuthService,
    private jwt: JWTUtils,
  ) {}

  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatPaginator) paginator!: MatPaginator;

  ngOnInit(): void {
    const token = this.cookieService.get('token');
    const permissionLevel = this.perm.checkPermission(token);
    this.userType = permissionLevel;
    const jwtType = (this.jwt.getUserTypeFromJWT(token) || '').toLowerCase();
    this.canAccessManagement =
      permissionLevel === 'SuperAdmin' || jwtType === 'associate';
    this.currentUserId = this.jwt.getUserIDFromJWT();

    this.route.queryParamMap.subscribe(qp => {
      const mainF = qp.get('mainFilter') as 'all' | 'mine' | 'workspace' | null;
      this.mainFilter = mainF || 'all';
      const statusF = qp.get('statusFilter') as 'open' | 'in_progress' | 'resolved' | null;
      this.statusFilter = statusF || undefined;

      const qPage = Number(qp.get('page'));
      this.pageIndex = isNaN(qPage) || qPage < 1 ? 0 : qPage - 1;

      const qPageSize = Number(qp.get('page_size'));
      this.pageSize = !isNaN(qPageSize) && qPageSize > 0 ? qPageSize : this.pageSize;

      const qOrdering = qp.get('ordering');
      if (qOrdering) {
        this.sortDirection = qOrdering.startsWith('-') ? 'desc' : 'asc';
        this.sortActive = qOrdering.replace(/^-/, '');
      } else {
        this.initDefaultSorting();
      }

      const raw = qp.get('projects');
      this.selectedProjectIds = raw
        ? raw.split(',').map(s => parseInt(s, 10)).filter(n => !isNaN(n) && n > 0)
        : [];

      this.loadTickets();
    });

    this.loadProjectList();
  }

  private loadProjectList(): void {
    this.apiProject.projectList().pipe(
      catchError(err => {
        console.error('Errore API projectList', err);
        return of({ data: [] });
      })
    ).subscribe((res: any) => {
      this.projectList = res?.data ?? [];
    });
  }

  onProjectFilterChange(): void {
    this.pageIndex = 0;
    this.updateUrlParams();
    this.loadTickets();
  }

  private initDefaultSorting(): void {
    if (this.mainFilter === 'mine') {
      this.sortActive = 'priority_custom';
      this.sortDirection = 'asc';
    } else {
      this.sortActive = 'opening_date';
      this.sortDirection = 'desc';
    }
  }

  selectMainFilter(filterKey: 'all' | 'mine' | 'workspace'): void {
    this.mainFilter = filterKey;
    this.pageIndex = 0;
    this.initDefaultSorting();
    this.updateUrlParams();
    this.loadTickets();
  }

  selectStatusFilter(filterKey: 'open' | 'in_progress' | 'resolved' | undefined): void {
    this.statusFilter = filterKey;
    this.pageIndex = 0;
    this.updateUrlParams();
    this.loadTickets();
  }

  private loadTickets(): void {
    const ordering = this.sortActive
      ? (this.sortDirection === 'desc' ? `-${this.sortActive}` : this.sortActive)
      : undefined;

    const params: any = {
      page: this.pageIndex + 1,
      page_size: this.pageSize,
      ordering,
    };

    if (this.mainFilter === 'all') {
      if (this.statusFilter) params.status = this.statusFilter;
    } else if (this.mainFilter === 'mine') {
      params.mine = 'true';
      if (this.statusFilter) params.status = this.statusFilter;
    } else if (this.mainFilter === 'workspace') {
      params.workspace_open = 'true';
      if (this.statusFilter) params.status = this.statusFilter;
    }

    if (this.selectedProjectIds.length > 0) {
      params['project__in'] = this.selectedProjectIds.join(',');
    }

    this.apiTicket.ticketList(params)
      .pipe(
        catchError(err => {
          console.error('Errore API ticketList', err);
          this.tickets = [];
          this.total = 0;
          return of({ count: 0, results: [] });
        })
      )
      .subscribe((resp: any) => {
        this.tickets = resp.results;
        this.total = resp.count;
      });
  }

  onPageChange(e: PageEvent): void {
    this.pageIndex = e.pageIndex;
    this.pageSize = e.pageSize;
    this.updateUrlParams(true);
    this.loadTickets();
  }

  onSortChange(sort: Sort): void {
    this.sortActive = sort.active;
    this.sortDirection = sort.direction || 'asc';
    this.pageIndex = 0;
    this.updateUrlParams();
    this.loadTickets();
  }

  private updateUrlParams(pushHistory = false): void {
    const ordering =
      this.sortDirection === 'desc' ? `-${this.sortActive}` : this.sortActive;

    const params: Params = {
      mainFilter: this.mainFilter,
      page: this.pageIndex + 1,
      page_size: this.pageSize,
      ordering,
      statusFilter: this.statusFilter ?? null,
      projects: this.selectedProjectIds.length ? this.selectedProjectIds.join(',') : null,
    };

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: params,
      queryParamsHandling: 'merge',
      replaceUrl: !pushHistory
    });
  }

  redirectTo(url: string) {
    this.router.navigate([url]);
  }

  truncate(text: string, limit: number) {
    return text?.length > limit ? text.substring(0, limit) + '...' : text;
  }

  trasformDateHours(date: string) {
    return this.dataParser.ISOToNormalDate(date);
  }

  getDisplayedColumns() {
    return this.userType !== 'Utente'
      ? this.displayedAdminColumns
      : this.displayedClientColumns;
  }

  getFullName(u: any): string {
    const fn = u?.first_name?.trim() || '';
    const ln = u?.last_name?.trim() || '';
    return `${fn} ${ln}`.trim() || u?.username || u?.email || 'Utente';
  }

  getInitials(u: any): string {
    const fn = u?.first_name?.[0] || '';
    const ln = u?.last_name?.[0] || '';
    return `${fn}${ln}`.toUpperCase() || '?';
  }

  getPriorityClass(p: string) {
    return p === 'high'
      ? 'high-priority'
      : p === 'medium'
      ? 'medium-priority'
      : 'low-priority';
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

  isAwaitingResponse(t: any): boolean {
    if (t?.status === 'resolved') return false;
    const lm = t?.last_message;
    if (!lm?.author) return false;
    const p = lm.author.permission;
    return (p === 50 || p === 100) && lm.author.id !== this.currentUserId;
  }

  getProjectLabel(t: any): string | null {
    const p = t?.project;
    if (!p) return null;

    if (typeof p === 'object' && p.title) return p.title;
    if (typeof p === 'number') return `Progetto #${p}`;
    return null;
  }
}
