import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { Account, Category, Transaction } from 'src/app/models/finance';

@Component({
  selector: 'app-transaction-edit',
  templateUrl: './transaction-edit.component.html',
  styleUrls: ['./transaction-edit.component.css']
})
export class TransactionEditComponent implements OnInit {

  transactionForm!: FormGroup;
  transaction: Transaction | null = null;
  accounts: Account[] = [];
  categories: Category[] = [];
  loading = true;
  saving = false;
  transactionId!: number;

  typeOptions = [
    { value: 'income', label: 'Entrata' },
    { value: 'expense', label: 'Uscita' }
  ];

  statusOptions = [
    { value: 'pending', label: 'In attesa' },
    { value: 'scheduled', label: 'Programmato' },
    { value: 'paid', label: 'Pagato' },
    { value: 'cancelled', label: 'Annullato' }
  ];

  vatOptions = [
    { value: 0, label: 'Nessuna IVA (0%)' },
    { value: 4, label: '4%' },
    { value: 10, label: '10%' },
    { value: 22, label: '22%' }
  ];

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: FinanceApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.loadData();
    
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.transactionId = +id;
        this.loadTransaction();
      }
    });
  }

  private initForm(): void {
    this.transactionForm = this.fb.group({
      account: [null, Validators.required],
      category: [null, Validators.required],
      description: ['', [Validators.required, Validators.maxLength(500)]],
      gross_amount: [null, [Validators.required, Validators.min(0.01)]],
      vat_percentage: [0],
      competence_date: ['', Validators.required],
      payment_date: [null],
      transaction_type: ['expense', Validators.required],
      status: ['pending', Validators.required],
      is_hypothetical: [false],
      external_reference: [''],
      notes: ['']
    });
  }

  private loadData(): void {
    this.api.accountList({ is_active: true }).subscribe(accounts => {
      this.accounts = accounts;
    });
    this.api.categoryList({ is_active: true }).subscribe(categories => {
      this.categories = categories;
    });
  }

  private loadTransaction(): void {
    this.api.transactionDetail(this.transactionId).subscribe({
      next: (transaction) => {
        this.transaction = transaction;
        this.patchForm(transaction);
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

  private patchForm(t: Transaction): void {
    this.transactionForm.patchValue({
      account: t.account?.id || (t as any).account_id,
      category: t.category?.id || (t as any).category_id,
      description: t.description,
      gross_amount: t.gross_amount,
      vat_percentage: t.vat_percentage,
      competence_date: t.competence_date,
      payment_date: t.payment_date,
      transaction_type: t.transaction_type,
      status: t.status,
      is_hypothetical: t.is_hypothetical,
      external_reference: t.external_reference,
      notes: t.notes
    });
  }

  getFilteredCategories(): Category[] {
    const type = this.transactionForm.get('transaction_type')?.value;
    return this.categories.filter(c => 
      !c.transaction_type || c.transaction_type === type
    );
  }

  onSubmit(): void {
    if (this.transactionForm.invalid) {
      this.markFormTouched();
      return;
    }

    this.saving = true;
    const formData = this.transactionForm.value;

    const data = {
      account: formData.account,
      category: formData.category,
      description: formData.description,
      gross_amount: formData.gross_amount,
      vat_percentage: formData.vat_percentage || 0,
      competence_date: formData.competence_date,
      payment_date: formData.payment_date || null,
      transaction_type: formData.transaction_type,
      status: formData.status,
      is_hypothetical: formData.is_hypothetical,
      external_reference: formData.external_reference || null,
      notes: formData.notes || null
    };

    this.api.transactionUpdate(this.transactionId, data).subscribe({
      next: () => {
        this.saving = false;
        this.snackBar.open('Movimento aggiornato con successo', 'OK', { duration: 3000 });
        this.router.navigate(['/finance', this.transactionId]);
      },
      error: (err) => {
        this.saving = false;
        console.error('Errore aggiornamento movimento', err);
        this.snackBar.open('Errore durante l\'aggiornamento', 'Chiudi', { duration: 5000 });
      }
    });
  }

  private markFormTouched(): void {
    Object.keys(this.transactionForm.controls).forEach(key => {
      this.transactionForm.get(key)?.markAsTouched();
    });
  }

  cancel(): void {
    this.router.navigate(['/finance', this.transactionId]);
  }

  onTypeChange(): void {
    // Optionally reset category when type changes
  }
}
