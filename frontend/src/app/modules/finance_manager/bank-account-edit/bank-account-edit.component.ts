import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { Bank, Account } from 'src/app/models/finance';

@Component({
  selector: 'app-bank-account-edit',
  templateUrl: './bank-account-edit.component.html',
  styleUrls: ['./bank-account-edit.component.css']
})
export class BankAccountEditComponent implements OnInit {

  accountForm!: FormGroup;
  bankForm!: FormGroup;
  banks: Bank[] = [];
  
  entityType: 'account' | 'bank' = 'account';
  isEditMode = false;
  entityId: number | null = null;
  loading = true;
  saving = false;

  accountTypeOptions = [
    { value: 'checking', label: 'Conto Corrente' },
    { value: 'savings', label: 'Conto Risparmio' },
    { value: 'business', label: 'Conto Business' },
    { value: 'cash', label: 'Contanti' },
    { value: 'investment', label: 'Investimenti' },
    { value: 'credit_card', label: 'Carta di Credito' },
    { value: 'other', label: 'Altro' }
  ];

  get bankOptions(): Array<{ id: number | null; name: string }> {
    return [{ id: null, name: 'Nessuna (Contanti/Altro)' }, ...this.banks];
  }

  currencyOptions = [
    { value: 'EUR', label: 'Euro (€)' },
    { value: 'USD', label: 'Dollaro USA ($)' },
    { value: 'GBP', label: 'Sterlina (£)' },
    { value: 'CHF', label: 'Franco Svizzero (CHF)' }
  ];

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: FinanceApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.initForms();
    this.loadBanks();
    
    this.route.queryParamMap.subscribe(qp => {
      this.entityType = (qp.get('type') as 'account' | 'bank') || 'account';
    });
    
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.isEditMode = true;
        this.entityId = +id;
        this.loadEntity();
      } else {
        this.loading = false;
      }
    });
  }

  private initForms(): void {
    this.accountForm = this.fb.group({
      name: ['', [Validators.required, Validators.maxLength(200)]],
      bank_id: [null],
      iban: ['', Validators.maxLength(34)],
      initial_balance: [0, Validators.required],
      currency: ['EUR', Validators.required],
      account_type: ['checking', Validators.required],
      description: [''],
      is_active: [true],
      include_in_totals: [true],
      color: ['#2196f3']
    });

    this.bankForm = this.fb.group({
      name: ['', [Validators.required, Validators.maxLength(200)]],
      abi_code: ['', Validators.maxLength(10)],
      swift_code: ['', Validators.maxLength(11)],
      country: ['IT', Validators.maxLength(2)],
      website: [''],
      notes: [''],
      is_active: [true]
    });
  }

  private loadBanks(): void {
    this.api.bankList({ is_active: true }).subscribe(banks => {
      this.banks = banks;
    });
  }

  private loadEntity(): void {
    if (this.entityType === 'account') {
      this.api.accountDetail(this.entityId!).subscribe({
        next: (account) => {
          this.patchAccountForm(account);
          this.loading = false;
        },
        error: (err) => {
          console.error('Errore caricamento conto', err);
          this.loading = false;
          this.snackBar.open('Conto non trovato', 'Chiudi', { duration: 3000 });
          this.router.navigate(['/finance/accounts']);
        }
      });
    } else {
      this.api.bankDetail(this.entityId!).subscribe({
        next: (bank) => {
          this.patchBankForm(bank);
          this.loading = false;
        },
        error: (err) => {
          console.error('Errore caricamento banca', err);
          this.loading = false;
          this.snackBar.open('Banca non trovata', 'Chiudi', { duration: 3000 });
          this.router.navigate(['/finance/accounts']);
        }
      });
    }
  }

  private patchAccountForm(account: Account): void {
    this.accountForm.patchValue({
      name: account.name,
      bank_id: account.bank?.id || account.bank_id,
      iban: account.iban,
      initial_balance: account.initial_balance,
      currency: account.currency,
      account_type: account.account_type,
      description: account.description,
      is_active: account.is_active,
      include_in_totals: account.include_in_totals,
      color: account.color
    });
  }

  private patchBankForm(bank: Bank): void {
    this.bankForm.patchValue({
      name: bank.name,
      abi_code: bank.abi_code,
      swift_code: bank.swift_code,
      country: bank.country,
      website: bank.website,
      notes: bank.notes,
      is_active: bank.is_active
    });
  }

  setEntityType(type: 'account' | 'bank'): void {
    this.entityType = type;
  }

  onSubmit(): void {
    if (this.entityType === 'account') {
      this.saveAccount();
    } else {
      this.saveBank();
    }
  }

  private saveAccount(): void {
    if (this.accountForm.invalid) {
      this.markFormTouched(this.accountForm);
      return;
    }

    this.saving = true;
    const data = this.accountForm.value;

    const request = this.isEditMode
      ? this.api.accountUpdate(this.entityId!, data)
      : this.api.accountCreate(data);

    request.subscribe({
      next: () => {
        this.saving = false;
        this.snackBar.open(
          this.isEditMode ? 'Conto aggiornato' : 'Conto creato',
          'OK',
          { duration: 3000 }
        );
        this.router.navigate(['/finance/accounts']);
      },
      error: (err) => {
        this.saving = false;
        console.error('Errore salvataggio', err);
        this.snackBar.open('Errore durante il salvataggio', 'Chiudi', { duration: 5000 });
      }
    });
  }

  private saveBank(): void {
    if (this.bankForm.invalid) {
      this.markFormTouched(this.bankForm);
      return;
    }

    this.saving = true;
    const data = this.bankForm.value;

    const request = this.isEditMode
      ? this.api.bankUpdate(this.entityId!, data)
      : this.api.bankCreate(data);

    request.subscribe({
      next: () => {
        this.saving = false;
        this.snackBar.open(
          this.isEditMode ? 'Banca aggiornata' : 'Banca creata',
          'OK',
          { duration: 3000 }
        );
        this.router.navigate(['/finance/accounts'], { queryParams: { tab: 'banks' } });
      },
      error: (err) => {
        this.saving = false;
        console.error('Errore salvataggio', err);
        this.snackBar.open('Errore durante il salvataggio', 'Chiudi', { duration: 5000 });
      }
    });
  }

  private markFormTouched(form: FormGroup): void {
    Object.keys(form.controls).forEach(key => {
      form.get(key)?.markAsTouched();
    });
  }

  cancel(): void {
    this.router.navigate(['/finance/accounts']);
  }
}
