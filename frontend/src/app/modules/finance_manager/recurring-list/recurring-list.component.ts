import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { RecurrenceRule } from 'src/app/models/finance';

@Component({
  selector: 'app-recurring-list',
  templateUrl: './recurring-list.component.html',
  styleUrls: ['./recurring-list.component.css']
})
export class RecurringListComponent implements OnInit {

  rules: RecurrenceRule[] = [];
  loading = false;
  
  // Filters
  showInactive = false;
  filterType: string | null = null;

  displayedColumns = [
    'name', 'category', 'account', 'type', 'amount', 
    'frequency', 'next_occurrence', 'status', 'actions'
  ];

  constructor(
    private api: FinanceApiService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadRules();
  }

  loadRules(): void {
    this.loading = true;
    
    const params: any = {};
    if (!this.showInactive) {
      params.is_active = true;
    }
    if (this.filterType) {
      params.type = this.filterType;
    }

    this.api.recurrenceRuleList(params).subscribe({
      next: (rules) => {
        this.rules = rules;
        this.loading = false;
      },
      error: (err) => {
        console.error('Errore caricamento regole', err);
        this.loading = false;
      }
    });
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }

  editRule(id: number): void {
    this.router.navigate(['/finance/recurring/edit', id]);
  }

  deleteRule(rule: RecurrenceRule): void {
    if (confirm(`Eliminare la regola "${rule.name}"?`)) {
      this.api.recurrenceRuleDelete(rule.id).subscribe({
        next: () => {
          this.snackBar.open('Regola eliminata', 'OK', { duration: 3000 });
          this.loadRules();
        },
        error: (err) => {
          console.error('Errore eliminazione', err);
          this.snackBar.open('Errore durante l\'eliminazione', 'Chiudi', { duration: 5000 });
        }
      });
    }
  }

  generateNow(rule: RecurrenceRule): void {
    this.api.recurrenceRuleGenerate(rule.id).subscribe({
      next: (result) => {
        this.snackBar.open('Movimento generato con successo', 'OK', { duration: 3000 });
        this.loadRules();
      },
      error: (err) => {
        console.error('Errore generazione', err);
        this.snackBar.open('Errore durante la generazione', 'Chiudi', { duration: 5000 });
      }
    });
  }

  toggleActive(rule: RecurrenceRule): void {
    this.api.recurrenceRuleUpdate(rule.id, { is_active: !rule.is_active } as any).subscribe({
      next: () => {
        rule.is_active = !rule.is_active;
        this.snackBar.open(
          rule.is_active ? 'Regola attivata' : 'Regola disattivata',
          'OK',
          { duration: 3000 }
        );
      },
      error: (err) => {
        console.error('Errore aggiornamento', err);
      }
    });
  }

  onFilterChange(): void {
    this.loadRules();
  }

  getTypeLabel(type: string): string {
    return type === 'income' ? 'Entrata' : 'Uscita';
  }

  getTypeClass(type: string): string {
    return type === 'income' ? 'type-income' : 'type-expense';
  }

  getFrequencyLabel(freq: string): string {
    const labels: Record<string, string> = {
      'daily': 'Giornaliero',
      'weekly': 'Settimanale',
      'biweekly': 'Bisettimanale',
      'monthly': 'Mensile',
      'bimonthly': 'Bimestrale',
      'quarterly': 'Trimestrale',
      'semiannual': 'Semestrale',
      'annual': 'Annuale'
    };
    return labels[freq] || freq;
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('it-IT');
  }
}
