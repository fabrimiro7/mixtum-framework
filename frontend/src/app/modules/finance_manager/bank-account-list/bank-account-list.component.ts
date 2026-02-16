import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { Bank, Account, AggregateBalanceResponse } from 'src/app/models/finance';

@Component({
  selector: 'app-bank-account-list',
  templateUrl: './bank-account-list.component.html',
  styleUrls: ['./bank-account-list.component.css']
})
export class BankAccountListComponent implements OnInit {

  banks: Bank[] = [];
  accounts: Account[] = [];
  aggregateBalance: AggregateBalanceResponse | null = null;
  
  loading = false;
  activeTab: 'accounts' | 'banks' = 'accounts';
  showInactive = false;

  accountColumns = ['name', 'bank', 'type', 'iban', 'balance', 'status', 'actions'];
  bankColumns = ['name', 'abi_code', 'swift_code', 'accounts_count', 'status', 'actions'];

  accountTypeLabels: Record<string, string> = {
    'checking': 'Conto Corrente',
    'savings': 'Conto Risparmio',
    'business': 'Conto Business',
    'cash': 'Contanti',
    'investment': 'Investimenti',
    'credit_card': 'Carta di Credito',
    'other': 'Altro'
  };

  constructor(
    private api: FinanceApiService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    this.loadAccounts();
    this.loadBanks();
    this.loadAggregateBalance();
  }

  private loadAccounts(): void {
    const params: any = {};
    if (!this.showInactive) {
      params.is_active = true;
    }
    
    this.api.accountList(params).subscribe({
      next: (accounts) => {
        this.accounts = accounts;
        this.loading = false;
      },
      error: (err) => {
        console.error('Errore caricamento conti', err);
        this.loading = false;
      }
    });
  }

  private loadBanks(): void {
    const params: any = {};
    if (!this.showInactive) {
      params.is_active = true;
    }
    
    this.api.bankList(params).subscribe({
      next: (banks) => {
        this.banks = banks;
      }
    });
  }

  private loadAggregateBalance(): void {
    this.api.getAggregateBalance('EUR').subscribe({
      next: (resp) => {
        this.aggregateBalance = resp;
      }
    });
  }

  setTab(tab: 'accounts' | 'banks'): void {
    this.activeTab = tab;
  }

  onFilterChange(): void {
    this.loadData();
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }

  addAccount(): void {
    this.router.navigate(['/finance/accounts/add'], { queryParams: { type: 'account' } });
  }

  addBank(): void {
    this.router.navigate(['/finance/accounts/add'], { queryParams: { type: 'bank' } });
  }

  editAccount(id: number): void {
    this.router.navigate(['/finance/accounts/edit', id], { queryParams: { type: 'account' } });
  }

  editBank(id: number): void {
    this.router.navigate(['/finance/accounts/edit', id], { queryParams: { type: 'bank' } });
  }

  deleteAccount(account: Account): void {
    if (confirm(`Eliminare il conto "${account.name}"?`)) {
      this.api.accountDelete(account.id).subscribe({
        next: () => {
          this.snackBar.open('Conto eliminato', 'OK', { duration: 3000 });
          this.loadAccounts();
        },
        error: (err) => {
          console.error('Errore eliminazione', err);
          this.snackBar.open('Errore durante l\'eliminazione', 'Chiudi', { duration: 5000 });
        }
      });
    }
  }

  deleteBank(bank: Bank): void {
    if (confirm(`Eliminare la banca "${bank.name}"? Tutti i conti associati rimarranno senza banca.`)) {
      this.api.bankDelete(bank.id).subscribe({
        next: () => {
          this.snackBar.open('Banca eliminata', 'OK', { duration: 3000 });
          this.loadBanks();
        },
        error: (err) => {
          console.error('Errore eliminazione', err);
          this.snackBar.open('Errore durante l\'eliminazione', 'Chiudi', { duration: 5000 });
        }
      });
    }
  }

  getAccountTypeLabel(type: string): string {
    return this.accountTypeLabels[type] || type;
  }

  formatCurrency(amount: number | undefined): string {
    if (amount === undefined) return '-';
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  formatIban(iban: string | undefined): string {
    if (!iban) return '-';
    // Format IBAN with spaces every 4 characters
    return iban.replace(/(.{4})/g, '$1 ').trim();
  }

  getTotalBalance(): number {
    return this.aggregateBalance?.total_balance || 0;
  }
}
