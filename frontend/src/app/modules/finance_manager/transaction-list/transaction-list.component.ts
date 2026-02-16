import { Component, OnInit, ViewChild } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatSort, Sort } from '@angular/material/sort';
import { catchError, of } from 'rxjs';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { Transaction, TransactionListParams, Account, Category, TransactionType, TransactionStatus } from 'src/app/models/finance';

@Component({
  selector: 'app-transaction-list',
  templateUrl: './transaction-list.component.html',
  styleUrls: ['./transaction-list.component.css']
})
export class TransactionListComponent implements OnInit {

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  transactions: Transaction[] = [];
  accounts: Account[] = [];
  categories: Category[] = [];

  // Filters
  selectedAccount: number | null = null;
  selectedCategory: number | null = null;
  selectedType: TransactionType | null = null;
  selectedStatus: TransactionStatus | null = null;
  selectedPeriod: string = 'this_month';
  searchText: string = '';

  // Pagination
  total = 0;
  pageIndex = 0;
  pageSize = 50;
  pageSizeOptions = [25, 50, 100];

  // Sorting
  sortActive = 'competence_date';
  sortDirection: 'asc' | 'desc' = 'desc';

  // UI
  loading = false;
  displayedColumns = [
    'competence_date', 'description', 'category', 'account', 
    'type', 'gross_amount', 'status', 'actions'
  ];

  typeOptions: Array<{ value: TransactionType; label: string }> = [
    { value: 'income', label: 'Entrata' },
    { value: 'expense', label: 'Uscita' }
  ];

  statusOptions: Array<{ value: TransactionStatus; label: string }> = [
    { value: 'pending', label: 'In attesa' },
    { value: 'scheduled', label: 'Programmato' },
    { value: 'paid', label: 'Pagato' },
    { value: 'cancelled', label: 'Annullato' }
  ];

  periodOptions = [
    { value: 'this_month', label: 'Mese corrente' },
    { value: 'last_month', label: 'Mese scorso' },
    { value: 'last_3_months', label: 'Ultimi 3 mesi' },
    { value: 'this_year', label: 'Anno corrente' },
    { value: '', label: 'Tutti' }
  ];

  get accountFilterOptions(): Array<{ id: number | null; name: string }> {
    return [{ id: null, name: 'Tutti' }, ...this.accounts];
  }

  get categoryFilterOptions(): Array<{ id: number | null; name: string }> {
    return [{ id: null, name: 'Tutte' }, ...this.categories];
  }

  get typeFilterOptions(): Array<{ value: TransactionType | null; label: string }> {
    return [{ value: null, label: 'Tutti' }, ...this.typeOptions];
  }

  get statusFilterOptions(): Array<{ value: TransactionStatus | null; label: string }> {
    return [{ value: null, label: 'Tutti' }, ...this.statusOptions];
  }

  constructor(
    private api: FinanceApiService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.loadFiltersData();
    this.loadTransactions();
  }

  private loadFiltersData(): void {
    this.api.accountList({ is_active: true }).subscribe(accounts => {
      this.accounts = accounts;
    });
    this.api.categoryList({ is_active: true }).subscribe(categories => {
      this.categories = categories;
    });
  }

  loadTransactions(): void {
    this.loading = true;

    const params: TransactionListParams = {
      page: this.pageIndex + 1,
      page_size: this.pageSize,
      ordering: this.sortDirection === 'desc' ? `-${this.sortActive}` : this.sortActive
    };

    if (this.selectedAccount) params.account = this.selectedAccount;
    if (this.selectedCategory) params.category = this.selectedCategory;
    if (this.selectedType) params.type = this.selectedType;
    if (this.selectedStatus) params.status = this.selectedStatus;
    if (this.selectedPeriod) params.period = this.selectedPeriod as any;
    if (this.searchText) params.search = this.searchText;

    this.api.transactionList(params)
      .pipe(
        catchError(err => {
          console.error('Errore caricamento movimenti', err);
          this.loading = false;
          return of({ count: 0, results: [] });
        })
      )
      .subscribe(resp => {
        this.transactions = resp.results;
        this.total = resp.count;
        this.loading = false;
      });
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.pageSize = event.pageSize;
    this.loadTransactions();
  }

  onSortChange(sort: Sort): void {
    this.sortActive = sort.active;
    this.sortDirection = (sort.direction || 'desc') as 'asc' | 'desc';
    this.pageIndex = 0;
    this.loadTransactions();
  }

  onFilterChange(): void {
    this.pageIndex = 0;
    this.loadTransactions();
  }

  clearFilters(): void {
    this.selectedAccount = null;
    this.selectedCategory = null;
    this.selectedType = null;
    this.selectedStatus = null;
    this.selectedPeriod = 'this_month';
    this.searchText = '';
    this.pageIndex = 0;
    this.loadTransactions();
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }

  viewDetail(id: number): void {
    this.router.navigate(['/finance', id]);
  }

  editTransaction(id: number): void {
    this.router.navigate(['/finance/edit', id]);
  }

  deleteTransaction(transaction: Transaction): void {
    if (confirm(`Eliminare il movimento "${transaction.description}"?`)) {
      this.api.transactionDelete(transaction.id).subscribe({
        next: () => this.loadTransactions(),
        error: err => console.error('Errore eliminazione', err)
      });
    }
  }

  markAsPaid(transaction: Transaction): void {
    this.api.transactionMarkPaid(transaction.id).subscribe({
      next: () => this.loadTransactions(),
      error: err => console.error('Errore aggiornamento', err)
    });
  }

  getTypeLabel(type: string): string {
    return type === 'income' ? 'Entrata' : 'Uscita';
  }

  getTypeClass(type: string): string {
    return type === 'income' ? 'type-income' : 'type-expense';
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      'pending': 'In attesa',
      'scheduled': 'Programmato',
      'paid': 'Pagato',
      'cancelled': 'Annullato'
    };
    return labels[status] || status;
  }

  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT');
  }

  truncate(text: string, limit: number): string {
    if (!text) return '';
    return text.length > limit ? text.substring(0, limit) + '...' : text;
  }
}
