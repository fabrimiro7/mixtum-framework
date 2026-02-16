import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { CashflowPeriod, Account, CategoryBreakdownItem } from 'src/app/models/finance';

@Component({
  selector: 'app-cashflow-chart',
  templateUrl: './cashflow-chart.component.html',
  styleUrls: ['./cashflow-chart.component.css']
})
export class CashflowChartComponent implements OnInit {

  // Chart Data
  cashflowData: any[] = [];
  categoryIncomeData: any[] = [];
  categoryExpenseData: any[] = [];

  // Chart Options
  chartType: 'bar' | 'line' = 'bar';
  granularity: 'month' | 'year' = 'month';
  
  // Filters
  accounts: Account[] = [];
  selectedAccount: number | null = null;
  dateFrom: string = '';
  dateTo: string = '';

  get accountFilterOptions(): Array<{ id: number | null; name: string }> {
    return [{ id: null, name: 'Tutti i conti' }, ...this.accounts];
  }

  // UI State
  loading = false;
  view: [number, number] = [900, 400];

  // Chart Config
  showXAxis = true;
  showYAxis = true;
  gradient = false;
  showLegend = true;
  showXAxisLabel = true;
  showYAxisLabel = true;
  xAxisLabel = 'Periodo';
  yAxisLabel = 'Importo (€)';
  legendPosition: 'right' | 'below' = 'below';

  colorScheme = {
    domain: ['#4caf50', '#f44336', '#2196f3']
  };

  categoryColorScheme = {
    domain: ['#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50', '#8bc34a']
  };

  // Totals
  totalIncome = 0;
  totalExpenses = 0;
  netCashflow = 0;

  constructor(
    private api: FinanceApiService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.setDefaultDates();
    this.loadAccounts();
    this.loadData();
  }

  private setDefaultDates(): void {
    const now = new Date();
    const startOfYear = new Date(now.getFullYear(), 0, 1);
    this.dateFrom = startOfYear.toISOString().split('T')[0];
    this.dateTo = now.toISOString().split('T')[0];
  }

  private loadAccounts(): void {
    this.api.accountList({ is_active: true }).subscribe(accounts => {
      this.accounts = accounts;
    });
  }

  loadData(): void {
    this.loading = true;
    this.loadCashflowSummary();
    this.loadCategoryBreakdown();
  }

  private loadCashflowSummary(): void {
    const params: any = {
      granularity: this.granularity
    };
    if (this.dateFrom) params.from = this.dateFrom;
    if (this.dateTo) params.to = this.dateTo;
    if (this.selectedAccount) params.account = this.selectedAccount;

    this.api.getCashflowSummary(params).subscribe({
      next: (resp) => {
        this.processCashflowData(resp.results);
        this.loading = false;
      },
      error: (err) => {
        console.error('Errore caricamento cashflow', err);
        this.loading = false;
      }
    });
  }

  private loadCategoryBreakdown(): void {
    const params: any = {};
    if (this.dateFrom) params.from = this.dateFrom;
    if (this.dateTo) params.to = this.dateTo;
    if (this.selectedAccount) params.account = this.selectedAccount;

    // Income breakdown
    this.api.getCategoryBreakdown({ ...params, type: 'income' }).subscribe({
      next: (resp) => {
        this.categoryIncomeData = resp.breakdown.map(item => ({
          name: item.category_name,
          value: item.total
        }));
      }
    });

    // Expense breakdown
    this.api.getCategoryBreakdown({ ...params, type: 'expense' }).subscribe({
      next: (resp) => {
        this.categoryExpenseData = resp.breakdown.map(item => ({
          name: item.category_name,
          value: item.total
        }));
      }
    });
  }

  private processCashflowData(periods: CashflowPeriod[]): void {
    this.totalIncome = 0;
    this.totalExpenses = 0;

    // Format for grouped bar chart
    this.cashflowData = periods.map(p => {
      this.totalIncome += p.total_income;
      this.totalExpenses += p.total_expenses;

      return {
        name: this.formatPeriodLabel(p.period),
        series: [
          { name: 'Entrate', value: p.total_income },
          { name: 'Uscite', value: p.total_expenses },
          { name: 'Netto', value: p.net_cashflow }
        ]
      };
    });

    this.netCashflow = this.totalIncome - this.totalExpenses;
  }

  private formatPeriodLabel(period: string): string {
    if (this.granularity === 'year') {
      return period;
    }
    // Format YYYY-MM to MMM YYYY
    const [year, month] = period.split('-');
    const months = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];
    return `${months[parseInt(month) - 1]} ${year}`;
  }

  onFilterChange(): void {
    this.loadData();
  }

  toggleChartType(): void {
    this.chartType = this.chartType === 'bar' ? 'line' : 'bar';
  }

  setGranularity(g: 'month' | 'year'): void {
    this.granularity = g;
    this.loadData();
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }

  // Chart value formatting
  yAxisTickFormatting = (value: number) => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    }
    if (value >= 1000) {
      return (value / 1000).toFixed(0) + 'K';
    }
    return value.toString();
  };
}
