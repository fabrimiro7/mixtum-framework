import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

import { FinanceApiService } from 'src/app/services/api/finance-api.service';
import { Account, Category, RecurrenceRule, RecurrenceRuleCreate } from 'src/app/models/finance';

@Component({
  selector: 'app-recurring-edit',
  templateUrl: './recurring-edit.component.html',
  styleUrls: ['./recurring-edit.component.css']
})
export class RecurringEditComponent implements OnInit {

  ruleForm!: FormGroup;
  accounts: Account[] = [];
  categories: Category[] = [];
  
  isEditMode = false;
  ruleId: number | null = null;
  loading = true;
  saving = false;

  typeOptions = [
    { value: 'income', label: 'Entrata' },
    { value: 'expense', label: 'Uscita' }
  ];

  frequencyOptions = [
    { value: 'daily', label: 'Giornaliero' },
    { value: 'weekly', label: 'Settimanale' },
    { value: 'biweekly', label: 'Bisettimanale' },
    { value: 'monthly', label: 'Mensile' },
    { value: 'bimonthly', label: 'Bimestrale' },
    { value: 'quarterly', label: 'Trimestrale' },
    { value: 'semiannual', label: 'Semestrale' },
    { value: 'annual', label: 'Annuale' }
  ];

  dayOfMonthOptions = Array.from({ length: 31 }, (_, i) => i + 1);
  dayOfWeekOptions = [
    { value: 0, label: 'Lunedì' },
    { value: 1, label: 'Martedì' },
    { value: 2, label: 'Mercoledì' },
    { value: 3, label: 'Giovedì' },
    { value: 4, label: 'Venerdì' },
    { value: 5, label: 'Sabato' },
    { value: 6, label: 'Domenica' }
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
        this.isEditMode = true;
        this.ruleId = +id;
        this.loadRule();
      } else {
        this.loading = false;
      }
    });
  }

  private initForm(): void {
    const today = new Date().toISOString().split('T')[0];
    
    this.ruleForm = this.fb.group({
      name: ['', [Validators.required, Validators.maxLength(200)]],
      account: [null, Validators.required],
      category: [null, Validators.required],
      description: ['', [Validators.required, Validators.maxLength(500)]],
      gross_amount: [null, [Validators.required, Validators.min(0.01)]],
      vat_percentage: [0],
      transaction_type: ['expense', Validators.required],
      frequency: ['monthly', Validators.required],
      day_of_month: [1],
      day_of_week: [null],
      start_date: [today, Validators.required],
      end_date: [null],
      is_active: [true],
      generate_as_hypothetical: [false],
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

  private loadRule(): void {
    this.api.recurrenceRuleDetail(this.ruleId!).subscribe({
      next: (rule) => {
        this.patchForm(rule);
        this.loading = false;
      },
      error: (err) => {
        console.error('Errore caricamento regola', err);
        this.loading = false;
        this.snackBar.open('Regola non trovata', 'Chiudi', { duration: 3000 });
        this.router.navigate(['/finance/recurring']);
      }
    });
  }

  private patchForm(rule: RecurrenceRule): void {
    this.ruleForm.patchValue({
      name: rule.name,
      account: rule.account?.id || (rule as any).account_id,
      category: rule.category?.id || (rule as any).category_id,
      description: rule.description,
      gross_amount: rule.gross_amount,
      vat_percentage: rule.vat_percentage,
      transaction_type: rule.transaction_type,
      frequency: rule.frequency,
      day_of_month: rule.day_of_month,
      day_of_week: rule.day_of_week,
      start_date: rule.start_date,
      end_date: rule.end_date,
      is_active: rule.is_active,
      generate_as_hypothetical: rule.generate_as_hypothetical,
      notes: rule.notes
    });
  }

  getFilteredCategories(): Category[] {
    const type = this.ruleForm.get('transaction_type')?.value;
    return this.categories.filter(c => !c.transaction_type || c.transaction_type === type);
  }

  showDayOfMonth(): boolean {
    const freq = this.ruleForm.get('frequency')?.value;
    return ['monthly', 'bimonthly', 'quarterly', 'semiannual', 'annual'].includes(freq);
  }

  showDayOfWeek(): boolean {
    const freq = this.ruleForm.get('frequency')?.value;
    return ['weekly', 'biweekly'].includes(freq);
  }

  onSubmit(): void {
    if (this.ruleForm.invalid) {
      this.markFormTouched();
      return;
    }

    this.saving = true;
    const formData = this.ruleForm.value;

    const data: RecurrenceRuleCreate = {
      name: formData.name,
      account: formData.account,
      category: formData.category,
      description: formData.description,
      gross_amount: formData.gross_amount,
      vat_percentage: formData.vat_percentage || 0,
      transaction_type: formData.transaction_type,
      frequency: formData.frequency,
      day_of_month: this.showDayOfMonth() ? formData.day_of_month : null,
      day_of_week: this.showDayOfWeek() ? formData.day_of_week : null,
      start_date: formData.start_date,
      end_date: formData.end_date || null,
      is_active: formData.is_active,
      generate_as_hypothetical: formData.generate_as_hypothetical,
      notes: formData.notes || null
    };

    const request = this.isEditMode
      ? this.api.recurrenceRuleUpdate(this.ruleId!, data)
      : this.api.recurrenceRuleCreate(data);

    request.subscribe({
      next: () => {
        this.saving = false;
        this.snackBar.open(
          this.isEditMode ? 'Regola aggiornata' : 'Regola creata',
          'OK',
          { duration: 3000 }
        );
        this.router.navigate(['/finance/recurring']);
      },
      error: (err) => {
        this.saving = false;
        console.error('Errore salvataggio', err);
        this.snackBar.open('Errore durante il salvataggio', 'Chiudi', { duration: 5000 });
      }
    });
  }

  private markFormTouched(): void {
    Object.keys(this.ruleForm.controls).forEach(key => {
      this.ruleForm.get(key)?.markAsTouched();
    });
  }

  cancel(): void {
    this.router.navigate(['/finance/recurring']);
  }
}
