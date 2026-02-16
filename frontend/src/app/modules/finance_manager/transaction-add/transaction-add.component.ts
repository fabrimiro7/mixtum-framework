import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { Account, Category, TransactionCreate } from 'src/app/models/finance';

@Component({
  selector: 'app-transaction-add',
  templateUrl: './transaction-add.component.html',
  styleUrls: ['./transaction-add.component.css']
})
export class TransactionAddComponent implements OnInit {

  transactionForm!: FormGroup;
  accounts: Account[] = [];
  categories: Category[] = [];
  loading = false;

  typeOptions = [
    { value: 'income', label: 'Entrata' },
    { value: 'expense', label: 'Uscita' }
  ];

  statusOptions = [
    { value: 'pending', label: 'In attesa' },
    { value: 'scheduled', label: 'Programmato' },
    { value: 'paid', label: 'Pagato' }
  ];

  vatOptions = [
    { value: 0, label: 'Nessuna IVA (0%)' },
    { value: 4, label: '4%' },
    { value: 10, label: '10%' },
    { value: 22, label: '22%' }
  ];

  constructor(
    private fb: FormBuilder,
    private api: FinanceApiService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.loadData();
  }

  private initForm(): void {
    const today = new Date().toISOString().split('T')[0];
    
    this.transactionForm = this.fb.group({
      account: [null, Validators.required],
      category: [null, Validators.required],
      description: ['', [Validators.required, Validators.maxLength(500)]],
      gross_amount: [null, [Validators.required, Validators.min(0.01)]],
      vat_percentage: [0],
      competence_date: [today, Validators.required],
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

    this.loading = true;
    const formData = this.transactionForm.value;

    const data: TransactionCreate = {
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

    this.api.transactionCreate(data).subscribe({
      next: (result) => {
        this.loading = false;
        this.snackBar.open('Movimento creato con successo', 'OK', { duration: 3000 });
        this.router.navigate(['/finance', result.id]);
      },
      error: (err) => {
        this.loading = false;
        console.error('Errore creazione movimento', err);
        this.snackBar.open('Errore durante la creazione', 'Chiudi', { duration: 5000 });
      }
    });
  }

  private markFormTouched(): void {
    Object.keys(this.transactionForm.controls).forEach(key => {
      this.transactionForm.get(key)?.markAsTouched();
    });
  }

  cancel(): void {
    this.router.navigate(['/finance']);
  }

  onTypeChange(): void {
    // Reset category when type changes
    this.transactionForm.patchValue({ category: null });
  }
}
