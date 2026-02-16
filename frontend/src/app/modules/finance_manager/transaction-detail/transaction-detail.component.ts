import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { Transaction } from 'src/app/models/finance';

@Component({
  selector: 'app-transaction-detail',
  templateUrl: './transaction-detail.component.html',
  styleUrls: ['./transaction-detail.component.css']
})
export class TransactionDetailComponent implements OnInit {

  transaction: Transaction | null = null;
  loading = true;
  transactionId!: number;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: FinanceApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.transactionId = +id;
        this.loadTransaction();
      }
    });
  }

  private loadTransaction(): void {
    this.loading = true;
    this.api.transactionDetail(this.transactionId).subscribe({
      next: (transaction) => {
        this.transaction = transaction;
        this.loading = false;
      },
      error: (err) => {
        console.error('Errore caricamento movimento', err);
        this.loading = false;
        this.snackBar.open('Movimento non trovato', 'Chiudi', { duration: 3000 });
        this.router.navigate(['/finance']);
      }
    });
  }

  edit(): void {
    this.router.navigate(['/finance/edit', this.transactionId]);
  }

  delete(): void {
    if (confirm('Eliminare questo movimento?')) {
      this.api.transactionDelete(this.transactionId).subscribe({
        next: () => {
          this.snackBar.open('Movimento eliminato', 'OK', { duration: 3000 });
          this.router.navigate(['/finance']);
        },
        error: (err) => {
          console.error('Errore eliminazione', err);
          this.snackBar.open('Errore durante l\'eliminazione', 'Chiudi', { duration: 5000 });
        }
      });
    }
  }

  markAsPaid(): void {
    this.api.transactionMarkPaid(this.transactionId).subscribe({
      next: (updated) => {
        this.transaction = updated;
        this.snackBar.open('Movimento segnato come pagato', 'OK', { duration: 3000 });
      },
      error: (err) => {
        console.error('Errore aggiornamento', err);
        this.snackBar.open('Errore durante l\'aggiornamento', 'Chiudi', { duration: 5000 });
      }
    });
  }

  back(): void {
    this.router.navigate(['/finance']);
  }

  getTypeLabel(type: string): string {
    return type === 'income' ? 'Entrata' : 'Uscita';
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

  getDataSourceLabel(source: string): string {
    const labels: Record<string, string> = {
      'manual': 'Inserimento manuale',
      'import_csv': 'Importazione CSV',
      'import_excel': 'Importazione Excel',
      'import_bank': 'Estratto conto',
      'recurring': 'Movimento ricorrente',
      'api': 'API'
    };
    return labels[source] || source;
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT');
  }
}
