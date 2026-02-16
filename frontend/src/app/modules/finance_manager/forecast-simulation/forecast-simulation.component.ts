import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { ForecastResult, ForecastPeriod, Account, Category, RecurrenceRule, TransactionCreate } from 'src/app/models/finance';

@Component({
  selector: 'app-forecast-simulation',
  templateUrl: './forecast-simulation.component.html',
  styleUrls: ['./forecast-simulation.component.css']
})
export class ForecastSimulationComponent implements OnInit {

  // Forecast data
  forecast: ForecastResult | null = null;
  forecastChartData: any[] = [];
  
  // Options
  months: number = 3;
  accounts: Account[] = [];
  selectedAccounts: number[] = [];
  includeHypothetical = true;
  includeRecurring = true;

  // Hypothetical transaction form
  showHypotheticalForm = false;
  hypotheticalForm!: FormGroup;
  categories: Category[] = [];
  
  // Recurring rules
  recurringRules: RecurrenceRule[] = [];
  
  // UI
  loading = false;
  view: [number, number] = [900, 350];

  colorScheme = {
    domain: ['#2196f3', '#4caf50', '#f44336']
  };

  constructor(
    private api: FinanceApiService,
    private fb: FormBuilder,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.loadData();
  }

  private initForm(): void {
    const today = new Date();
    const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
    
    this.hypotheticalForm = this.fb.group({
      account: [null, Validators.required],
      category: [null, Validators.required],
      description: ['', Validators.required],
      gross_amount: [null, [Validators.required, Validators.min(0.01)]],
      transaction_type: ['expense', Validators.required],
      competence_date: [nextMonth.toISOString().split('T')[0], Validators.required]
    });
  }

  private loadData(): void {
    this.api.accountList({ is_active: true }).subscribe(accounts => {
      this.accounts = accounts;
    });
    this.api.categoryList({ is_active: true }).subscribe(categories => {
      this.categories = categories;
    });
    this.api.recurrenceRuleList({ is_active: true }).subscribe(rules => {
      this.recurringRules = rules;
    });
    this.loadForecast();
  }

  loadForecast(): void {
    this.loading = true;
    
    const request = {
      months: this.months,
      account_ids: this.selectedAccounts.length > 0 ? this.selectedAccounts : undefined,
      include_hypothetical: this.includeHypothetical,
      include_recurring: this.includeRecurring,
      use_historical_averages: true,
      historical_months: 6
    };

    this.api.getForecast(request).subscribe({
      next: (result) => {
        this.forecast = result;
        this.processForecastData(result);
        this.loading = false;
      },
      error: (err) => {
        console.error('Errore caricamento previsione', err);
        this.loading = false;
        this.snackBar.open('Errore durante il caricamento della previsione', 'Chiudi', { duration: 5000 });
      }
    });
  }

  private processForecastData(result: ForecastResult): void {
    // Create balance projection chart data
    this.forecastChartData = result.periods.map(p => ({
      name: p.period_label,
      series: [
        { name: 'Saldo Proiettato', value: p.cumulative_balance },
        { name: 'Entrate', value: p.projected_income },
        { name: 'Uscite', value: p.projected_expenses }
      ]
    }));
  }

  setMonths(m: number): void {
    this.months = m;
    this.loadForecast();
  }

  onOptionsChange(): void {
    this.loadForecast();
  }

  toggleHypotheticalForm(): void {
    this.showHypotheticalForm = !this.showHypotheticalForm;
  }

  addHypotheticalTransaction(): void {
    if (this.hypotheticalForm.invalid) {
      Object.keys(this.hypotheticalForm.controls).forEach(key => {
        this.hypotheticalForm.get(key)?.markAsTouched();
      });
      return;
    }

    const formData = this.hypotheticalForm.value;
    
    const data: TransactionCreate = {
      account: formData.account,
      category: formData.category,
      description: formData.description,
      gross_amount: formData.gross_amount,
      competence_date: formData.competence_date,
      transaction_type: formData.transaction_type,
      status: 'pending',
      is_hypothetical: true
    };

    this.api.transactionCreate(data).subscribe({
      next: () => {
        this.snackBar.open('Movimento ipotetico aggiunto', 'OK', { duration: 3000 });
        this.hypotheticalForm.reset({
          transaction_type: 'expense',
          competence_date: this.hypotheticalForm.get('competence_date')?.value
        });
        this.showHypotheticalForm = false;
        this.loadForecast();
      },
      error: (err) => {
        console.error('Errore creazione movimento', err);
        this.snackBar.open('Errore durante la creazione', 'Chiudi', { duration: 5000 });
      }
    });
  }

  getFilteredCategories(): Category[] {
    const type = this.hypotheticalForm.get('transaction_type')?.value;
    return this.categories.filter(c => !c.transaction_type || c.transaction_type === type);
  }

  hasNegativeBalance(): boolean {
    if (!this.forecast) return false;
    return this.forecast.periods.some(p => p.cumulative_balance < 0);
  }

  getMinBalance(): number {
    if (!this.forecast) return 0;
    return Math.min(...this.forecast.periods.map(p => p.cumulative_balance));
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('it-IT');
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }

  yAxisTickFormatting = (value: number) => {
    if (Math.abs(value) >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    }
    if (Math.abs(value) >= 1000) {
      return (value / 1000).toFixed(0) + 'K';
    }
    return value.toString();
  };
}
