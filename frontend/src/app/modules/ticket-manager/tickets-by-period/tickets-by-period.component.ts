import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatSort, Sort } from '@angular/material/sort';
import { catchError, finalize, of, switchMap } from 'rxjs';

import { Ticket } from 'src/app/models/ticket';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { DateParser } from 'src/app/util/date_parse';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';

type StatsRow = {
  period: string;
  period_start: string;
  total: number;
  by_status: any;
  by_type: any;
  by_priority: any;
};

@Component({
  selector: 'app-tickets-by-period',
  templateUrl: './tickets-by-period.component.html',
  styleUrls: ['./tickets-by-period.component.css']
})
export class TicketsByPeriodComponent implements OnInit {

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  @Input() externalID: number = 0;
  @Input() minimal: boolean = false;

  projectId!: number;
  busyToggle = new Set<number>();

  // Chips
  years: number[] = [];
  monthsByYear: Record<number, { idx: number; label: string; count: number }[]> = {};
  selectedYear?: number;
  selectedMonthIdx?: number;

  // Data
  tickets: Ticket[] = [];
  total = 0;

  // Totali card
  minutesTotal = 0;
  quotesTotal = 0;

  // Tabella
  displayedColumns = [
    'id', 'title', 'ticket_type', 'client', 'status', 'payment_status', 'priority',
    'hours_estimation', 'cost_estimation', 'assignee', 'date', 'action'
  ];
  showTicketActions = true;
  pageIndex = 0;
  pageSize = 50;
  pageSizeOptions = [50, 125, 150, 200];
  sortActive: string = 'opening_date';
  sortDirection: 'asc' | 'desc' = 'desc';

  loadingStats = false;
  loadingTable = false;
  errorMsg: string | null = null;

  private avatarErrorMap = new WeakMap<any, boolean>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: TicketApiService,
    public dataParser: DateParser,
    private permissionService: PermissionService,
    private cookieService: CookieService,
  ) {}

  ngOnInit(): void {
    this.setActionVisibility();
    if (this.minimal) {
      this.displayedColumns = [
        'title', 'ticket_type', 'status', 'payment_status', 'priority',
        'date', 'hours_estimation', 'cost_estimation', 'action'
      ];
    }
    this.route.paramMap
      .pipe(
        switchMap(params => {
          const pid = Number(params.get('projectId') || params.get('id') || this.externalID || 0);
          this.projectId = pid;
          this.resetSelections();
          return this.loadStats();
        })
      )
      .subscribe();
  }

  // Chip handlers
  onYearClick(y: number) {
    if (this.selectedYear === y) {
      this.selectedYear = undefined;
      this.selectedMonthIdx = undefined;
      this.pageIndex = 0;
      this.tickets = [];
      this.total = 0;
      this.recomputeTotals();
      return;
    }
    this.selectedYear = y;
    this.selectedMonthIdx = undefined;
    this.pageIndex = 0;
    this.fetchTicketsForPeriod(y);
  }

  onMonthClick(mIdx: number) {
    if (this.selectedMonthIdx === mIdx) {
      this.selectedMonthIdx = undefined;
      this.pageIndex = 0;
      this.fetchTicketsForPeriod(this.selectedYear!);
      return;
    }
    this.selectedMonthIdx = mIdx;
    this.pageIndex = 0;
    this.fetchTicketsForPeriod(this.selectedYear!, mIdx);
  }

  isYearActive(y: number) { return this.selectedYear === y; }
  isMonthActive(mIdx: number) { return this.selectedMonthIdx === mIdx; }

  // Metodi usati nel template
  getYearTotal(y: number): number {
    const arr = this.monthsByYear?.[y] || [];
    return arr.reduce((sum, m) => sum + (m?.count ?? 0), 0);
  }

  monthsOfSelectedYear(): { idx: number; label: string; count: number }[] {
    return this.selectedYear ? (this.monthsByYear[this.selectedYear] || []) : [];
  }

  getAssigneesTooltip(list: any[] = []): string {
    return list.slice(1).map(a => this.getFullName(a)).join(', ');
  }

  // API
  private loadStats() {
    this.loadingStats = true;
    this.errorMsg = null;

    return this.api.getProjectTicketStats(this.projectId, {
      granularity: 'month',
      fill_gaps: 'true'
    }).pipe(
      catchError(err => {
        console.error('Errore loadStats', err);
        this.errorMsg = 'Errore nel caricamento delle statistiche.';
        this.loadingStats = false;
        return of(null);
      }),
      switchMap((res: any) => {
        this.loadingStats = false;
        if (!res || !Array.isArray(res.results)) return of(null);

        const results: StatsRow[] = res.results;
        this.computeYearMonthChips(results);

        // Autoselezione mese corrente: **chiama fetchTicketsForPeriod** (subscribe interno)
        const now = new Date();
        const cy = now.getFullYear();
        const cm = now.getMonth() + 1;

        if (this.monthsByYear[cy]?.some(m => m.idx === cm && m.count > 0)) {
          this.selectedYear = cy;
          this.selectedMonthIdx = cm;
          this.pageIndex = 0;
          this.fetchTicketsForPeriod(cy, cm);  // <— FIX: sottoscrive e popola
          return of(null);
        }

        // Fallback: anno più recente con dati (anche qui chiamiamo fetch)
        if (this.years.length) {
          this.selectedYear = Math.max(...this.years);
          this.selectedMonthIdx = undefined;
          this.pageIndex = 0;
          this.fetchTicketsForPeriod(this.selectedYear);
          return of(null);
        }

        return of(null);
      })
    );
  }

  private fetchTicketsForPeriod(year: number, monthIdx?: number) {
    this.loadingTable = true;
    this.errorMsg = null;

    this.fetchTicketsForPeriodObservable(year, monthIdx).subscribe((res: any) => {
      this.loadingTable = false;
      if (!res) return;
      this.tickets = res.results || res.data || [];
      this.total = res.count ?? res.total ?? this.tickets.length;
      this.recomputeTotals();
    });
  }

  private fetchTicketsForPeriodObservable(year: number, monthIdx?: number) {
    const { from, to } = this.makeRange(year, monthIdx);

    const params: any = {
      project: this.projectId,
      from,
      to,
      ordering: (this.sortDirection === 'asc' ? '' : '-') + this.sortActive,
      page: this.pageIndex + 1,
      page_size: this.pageSize,
    };

    return this.api.ticketList(params).pipe(
      catchError(err => {
        console.error('Errore listTickets', err);
        this.errorMsg = 'Errore nel caricamento dei ticket.';
        this.loadingTable = false;
        return of(null);
      })
    );
  }

  // Helpers
  private computeYearMonthChips(rows: StatsRow[]) {
    const byYear: Record<number, Record<number, number>> = {};
    rows.forEach(r => {
      if (!r.period?.includes('-')) return;
      const [yStr, mStr] = r.period.split('-');
      const y = Number(yStr);
      const m = Number(mStr);
      if (!byYear[y]) byYear[y] = {};
      byYear[y][m] = (byYear[y][m] || 0) + (r.total || 0);
    });

    this.years = Object.keys(byYear).map(Number).sort((a, b) => a - b);

    const itMonths = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'];

    this.monthsByYear = {};
    for (const y of this.years) {
      const months = Array.from({ length: 12 })
        .map((_, i) => ({ idx: i + 1, label: itMonths[i], count: byYear[y][i + 1] || 0 }))
        .filter(m => m.count > 0);
      if (months.length > 0) this.monthsByYear[y] = months;
    }
    this.years = this.years.filter(y => this.monthsByYear[y]?.length > 0);
  }

  monthLabel(mIdx: number): string {
    const it = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'];
    return it[(mIdx ?? 1) - 1] || '';
  }

  private makeRange(year: number, monthIdx?: number) {
    if (!monthIdx) {
      return { from: `${year}-01-01`, to: `${year}-12-31` };
    }
    const m = String(monthIdx).padStart(2, '0');
    const end = new Date(year, monthIdx, 0).getDate();
    return { from: `${year}-${m}-01`, to: `${year}-${m}-${String(end).padStart(2, '0')}` };
  }

  // Paginazione & sort
  onPageChange(e: PageEvent) {
    this.pageIndex = e.pageIndex;
    this.pageSize = e.pageSize;
    if (this.selectedYear) this.fetchTicketsForPeriod(this.selectedYear, this.selectedMonthIdx);
  }
  onSortChange(sort: Sort) {
    this.sortActive = sort.active;
    this.sortDirection = (sort.direction || 'asc') as ('asc' | 'desc');
    if (this.selectedYear) this.fetchTicketsForPeriod(this.selectedYear, this.selectedMonthIdx);
  }

  // UI helpers
  redirectTo(component: string) { this.router.navigate([component]); }
  trasformDateHours(dateStr: string) { return this.dataParser.ISOToNormalDate(dateStr); }
  truncate(text: string, limit: number) {
    const ellipsis = '...';
    return text?.length > limit ? text.substring(0, limit) + ellipsis : text;
  }

  getProjectLabel(t: any) {
    return t?.project?.name || t?.project?.title || (t?.project?.id ? `Project #${t?.project?.id}` : null);
  }
  getStatusClass(status: string) {
    return {
      'status-open': status === 'open',
      'status-in-progress': status === 'in_progress',
      'status-resolved': status === 'resolved',
      'status-closed': status === 'closed',
    };
  }
  getPriorityClass(priority: string | null) {
    const normalized = (priority || '').toString().toLowerCase();
    return {
      'low-priority': normalized === 'low',
      'medium-priority': normalized === 'medium',
      'high-priority': normalized === 'high',
    };
  }
  formatPriorityLabel(priority: string | null) {
    const normalized = (priority || '').toString().toLowerCase();
    if (normalized === 'low') return 'Bassa';
    if (normalized === 'medium') return 'Media';
    if (normalized === 'high') return 'Alta';
    return priority ? priority : '-';
  }
  getPaymentBadgeClass(paymentsStatus: boolean | null) {
    return {
      'payment-paid': paymentsStatus === true,
      'payment-unpaid': paymentsStatus === false,
    };
  }
  getFullName(u: any) {
    return [u?.first_name, u?.last_name].filter(Boolean).join(' ') || u?.username || u?.email || 'Utente';
  }
  getInitials(u: any) {
    const n = this.getFullName(u);
    const parts = n.split(' ');
    const letters = (parts[0]?.[0] || '') + (parts[1]?.[0] || '');
    return letters.toUpperCase();
  }
  hasAvatarError(obj: any) { return this.avatarErrorMap.get(obj) === true; }
  markAvatarError(obj: any) { this.avatarErrorMap.set(obj, true); }

  // Ticket type
  normalizeTypeLabel(type: any): string {
    const t = (type || '').toString().trim().toLowerCase();
    if (t === 'bug') return 'Bug';
    if (t === 'feature' || t === 'features') return 'Features';
    if (t === 'evolutiva' || t === 'evolution' || t === 'evolutionary' || t === 'evo') return 'Evolutiva';
    if (t === 'check') return 'Check';
    if (t === 'aggiornamento') return 'Aggiornamento';
    return type || '—';
  }
  getTicketTypeClass(type: any) {
    const t = (type || '').toString().trim().toLowerCase();
    return {
      'type-bug': t === 'bug',
      'type-feature': t === 'feature' || t === 'features',
      'type-evolutiva': t === 'evolutiva' || t === 'evolution' || t === 'evolutionary' || t === 'evo',
      'type-check': t === 'check',
      'type-aggiornamento': t === 'aggiornamento',
      'type-unknown': !['bug','feature','features','evolutiva','evolution','evolutionary','evo','check','aggiornamento'].includes(t),
    };
  }

  // Toggle pagamento
  togglePayments(t: Ticket) {
    console.log(t)
    if (!t?.id || this.busyToggle.has(t.id)) return;
    this.busyToggle.add(t.id);
    const prev = t.payments_status;
    t.payments_status = !prev;

    this.api.togglePaymentStatus(t.id)
      .pipe(finalize(() => this.busyToggle.delete(t.id)))
      .subscribe({
        next: (updated) => {
          console.log("update", updated)
          t.payments_status = (updated as any)?.payments_status ?? t.payments_status;
        },
        error: (err) => {
          console.error('Toggle payments_status fallito', err);
          t.payments_status = prev;
          this.errorMsg = 'Impossibile aggiornare lo stato pagamento del ticket.';
        }
      });
  }

  // Totali
  private toNumber(val: any): number {
    if (val === null || val === undefined) return 0;
    if (typeof val === 'number') return isNaN(val) ? 0 : val;
    let s = String(val).trim();
    if (!s) return 0;
    s = s.replace(/[^\d.,-]/g, '');
    if (s.indexOf(',') > -1 && s.indexOf('.') > -1) {
      if (s.lastIndexOf(',') > s.lastIndexOf('.')) {
        s = s.replace(/\./g, '').replace(',', '.');
      } else {
        s = s.replace(/,/g, '');
      }
    } else if (s.indexOf(',') > -1) {
      s = s.replace(',', '.');
    }
    const n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }
  private isBug(type: any): boolean {
    return (type || '').toString().trim().toLowerCase() === 'bug';
  }
  private isComplete(status: any): boolean {
    return (status || '').toString().trim().toLowerCase() === 'resolved';
  }
  private recomputeTotals() {
    let minTot = 0;
    let quoteTot = 0;
    for (const t of this.tickets) {
      minTot += this.toNumber((t as any).hours_estimation);
      if (!this.isBug((t as any).ticket_type) && this.isComplete((t as any).status)) {
        quoteTot += this.toNumber((t as any).cost_estimation);
      }
    }
    this.minutesTotal = Math.round(minTot);
    this.quotesTotal = quoteTot;
  }

  private resetSelections() {
    this.years = [];
    this.monthsByYear = {};
    this.selectedYear = undefined;
    this.selectedMonthIdx = undefined;
    this.tickets = [];
    this.total = 0;
    this.minutesTotal = 0;
    this.quotesTotal = 0;
    this.pageIndex = 0;
    this.sortActive = 'opening_date';
    this.sortDirection = 'desc';
  }

  private setActionVisibility() {
    const token = this.cookieService.get('token');
    if (!token) {
      this.showTicketActions = false;
      return;
    }
    let permission: string | null = null;
    try {
      permission = this.permissionService.checkPermission(token);
    } catch {
      permission = null;
    }
    this.showTicketActions = !(permission === 'Utente' || permission === 'Employee');
  }
}
