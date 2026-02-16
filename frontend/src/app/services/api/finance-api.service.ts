import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/django';
import {
  Bank,
  Account,
  Category,
  CategoryTree,
  Transaction,
  TransactionCreate,
  TransactionListParams,
  TransactionListResponse,
  CashflowSummaryResponse,
  CategoryBreakdownResponse,
  RecurrenceRule,
  RecurrenceRuleCreate,
  Budget,
  TaxConfig,
  ForecastResult,
  ForecastRequest,
  AggregateBalanceResponse,
  ImportResult
} from '../../models/finance';

@Injectable({
  providedIn: 'root'
})
export class FinanceApiService {

  private baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;
  private headers: HttpHeaders;

  constructor(
    private http: HttpClient,
    private cookieService: CookieService
  ) {
    let csrf = this.cookieService.get('csrftoken') || '';
    this.headers = new HttpHeaders()
      .set('content-type', 'application/json')
      .set('X-CSRFToken', csrf);
  }

  // =====================
  // Banks
  // =====================

  bankList(params?: { is_active?: boolean; search?: string }): Observable<Bank[]> {
    let httpParams = new HttpParams();
    if (params?.is_active !== undefined) {
      httpParams = httpParams.set('is_active', String(params.is_active));
    }
    if (params?.search) {
      httpParams = httpParams.set('search', params.search);
    }
    return this.http.get<Bank[]>(
      `${this.baseUrl}/api/finance_manager_accounts/banks/`,
      { headers: this.headers, params: httpParams }
    );
  }

  bankDetail(id: number): Observable<Bank> {
    return this.http.get<Bank>(
      `${this.baseUrl}/api/finance_manager_accounts/banks/${id}/`,
      { headers: this.headers }
    );
  }

  bankCreate(data: Partial<Bank>): Observable<Bank> {
    return this.http.post<Bank>(
      `${this.baseUrl}/api/finance_manager_accounts/banks/`,
      data,
      { headers: this.headers }
    );
  }

  bankUpdate(id: number, data: Partial<Bank>): Observable<Bank> {
    return this.http.patch<Bank>(
      `${this.baseUrl}/api/finance_manager_accounts/banks/${id}/`,
      data,
      { headers: this.headers }
    );
  }

  bankDelete(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/api/finance_manager_accounts/banks/${id}/`,
      { headers: this.headers }
    );
  }

  // =====================
  // Accounts
  // =====================

  accountList(params?: {
    is_active?: boolean;
    bank?: number;
    account_type?: string;
    currency?: string;
    search?: string;
  }): Observable<Account[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<Account[]>(
      `${this.baseUrl}/api/finance_manager_accounts/accounts/`,
      { headers: this.headers, params: httpParams }
    );
  }

  accountDetail(id: number): Observable<Account> {
    return this.http.get<Account>(
      `${this.baseUrl}/api/finance_manager_accounts/accounts/${id}/`,
      { headers: this.headers }
    );
  }

  accountCreate(data: Partial<Account>): Observable<Account> {
    return this.http.post<Account>(
      `${this.baseUrl}/api/finance_manager_accounts/accounts/`,
      data,
      { headers: this.headers }
    );
  }

  accountUpdate(id: number, data: Partial<Account>): Observable<Account> {
    return this.http.patch<Account>(
      `${this.baseUrl}/api/finance_manager_accounts/accounts/${id}/`,
      data,
      { headers: this.headers }
    );
  }

  accountDelete(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/api/finance_manager_accounts/accounts/${id}/`,
      { headers: this.headers }
    );
  }

  getAggregateBalance(currency: string = 'EUR', accountIds?: number[]): Observable<AggregateBalanceResponse> {
    let httpParams = new HttpParams().set('currency', currency);
    if (accountIds && accountIds.length > 0) {
      httpParams = httpParams.set('account_ids', accountIds.join(','));
    }
    return this.http.get<AggregateBalanceResponse>(
      `${this.baseUrl}/api/finance_manager_accounts/accounts/aggregate-balance/`,
      { headers: this.headers, params: httpParams }
    );
  }

  getBalanceByType(currency: string = 'EUR'): Observable<any> {
    return this.http.get<any>(
      `${this.baseUrl}/api/finance_manager_accounts/accounts/balance-by-type/`,
      { headers: this.headers, params: new HttpParams().set('currency', currency) }
    );
  }

  // =====================
  // Categories
  // =====================

  categoryList(params?: {
    is_active?: boolean;
    top_level?: boolean;
    parent?: number | 'null';
    transaction_type?: string;
    search?: string;
  }): Observable<Category[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<Category[]>(
      `${this.baseUrl}/api/finance_manager_core/categories/`,
      { headers: this.headers, params: httpParams }
    );
  }

  categoryTree(): Observable<CategoryTree[]> {
    return this.http.get<CategoryTree[]>(
      `${this.baseUrl}/api/finance_manager_core/categories/tree/`,
      { headers: this.headers }
    );
  }

  categoryDetail(id: number): Observable<Category> {
    return this.http.get<Category>(
      `${this.baseUrl}/api/finance_manager_core/categories/${id}/`,
      { headers: this.headers }
    );
  }

  categoryCreate(data: Partial<Category>): Observable<Category> {
    return this.http.post<Category>(
      `${this.baseUrl}/api/finance_manager_core/categories/`,
      data,
      { headers: this.headers }
    );
  }

  categoryUpdate(id: number, data: Partial<Category>): Observable<Category> {
    return this.http.patch<Category>(
      `${this.baseUrl}/api/finance_manager_core/categories/${id}/`,
      data,
      { headers: this.headers }
    );
  }

  // =====================
  // Transactions
  // =====================

  transactionList(params?: TransactionListParams): Observable<TransactionListResponse> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<TransactionListResponse>(
      `${this.baseUrl}/api/finance_manager_core/transactions/`,
      { headers: this.headers, params: httpParams }
    );
  }

  transactionDetail(id: number): Observable<Transaction> {
    return this.http.get<Transaction>(
      `${this.baseUrl}/api/finance_manager_core/transactions/${id}/`,
      { headers: this.headers }
    );
  }

  transactionCreate(data: TransactionCreate): Observable<Transaction> {
    return this.http.post<Transaction>(
      `${this.baseUrl}/api/finance_manager_core/transactions/`,
      data,
      { headers: this.headers }
    );
  }

  transactionUpdate(id: number, data: Partial<TransactionCreate>): Observable<Transaction> {
    return this.http.patch<Transaction>(
      `${this.baseUrl}/api/finance_manager_core/transactions/${id}/`,
      data,
      { headers: this.headers }
    );
  }

  transactionDelete(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/api/finance_manager_core/transactions/${id}/`,
      { headers: this.headers }
    );
  }

  transactionMarkPaid(id: number, paymentDate?: string): Observable<Transaction> {
    const body: any = {};
    if (paymentDate) {
      body.payment_date = paymentDate;
    }
    return this.http.post<Transaction>(
      `${this.baseUrl}/api/finance_manager_core/transactions/${id}/mark-paid/`,
      body,
      { headers: this.headers }
    );
  }

  transactionBulkUpdate(transactionIds: number[], updates: {
    status?: string;
    category_id?: number;
    payment_date?: string;
  }): Observable<{ updated_count: number; message: string }> {
    return this.http.post<{ updated_count: number; message: string }>(
      `${this.baseUrl}/api/finance_manager_core/transactions/bulk-update/`,
      { transaction_ids: transactionIds, ...updates },
      { headers: this.headers }
    );
  }

  transactionImport(data: {
    csv_content: string;
    account_id: number;
    default_category_id?: number;
    date_format?: string;
    skip_duplicates?: boolean;
    delimiter?: string;
  }): Observable<ImportResult> {
    return this.http.post<ImportResult>(
      `${this.baseUrl}/api/finance_manager_core/transactions/import/`,
      data,
      { headers: this.headers }
    );
  }

  // =====================
  // Cashflow Analytics
  // =====================

  getCashflowSummary(params?: {
    granularity?: 'month' | 'year';
    from?: string;
    to?: string;
    account?: number;
    include_hypothetical?: boolean;
  }): Observable<CashflowSummaryResponse> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<CashflowSummaryResponse>(
      `${this.baseUrl}/api/finance_manager_core/cashflow/summary/`,
      { headers: this.headers, params: httpParams }
    );
  }

  getCategoryBreakdown(params?: {
    type?: 'income' | 'expense';
    from?: string;
    to?: string;
    account?: number;
  }): Observable<CategoryBreakdownResponse> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<CategoryBreakdownResponse>(
      `${this.baseUrl}/api/finance_manager_core/cashflow/by-category/`,
      { headers: this.headers, params: httpParams }
    );
  }

  // =====================
  // Budgets
  // =====================

  budgetList(params?: {
    is_active?: boolean;
    category?: number;
    account?: number;
    period?: string;
    current?: boolean;
  }): Observable<Budget[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<Budget[]>(
      `${this.baseUrl}/api/finance_manager_planning/budgets/`,
      { headers: this.headers, params: httpParams }
    );
  }

  budgetStatus(): Observable<{
    total_budgets: number;
    over_budget: any[];
    near_limit: any[];
    healthy: any[];
  }> {
    return this.http.get<any>(
      `${this.baseUrl}/api/finance_manager_planning/budgets/status/`,
      { headers: this.headers }
    );
  }

  budgetCreate(data: Partial<Budget>): Observable<Budget> {
    return this.http.post<Budget>(
      `${this.baseUrl}/api/finance_manager_planning/budgets/`,
      data,
      { headers: this.headers }
    );
  }

  budgetUpdate(id: number, data: Partial<Budget>): Observable<Budget> {
    return this.http.patch<Budget>(
      `${this.baseUrl}/api/finance_manager_planning/budgets/${id}/`,
      data,
      { headers: this.headers }
    );
  }

  budgetDelete(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/api/finance_manager_planning/budgets/${id}/`,
      { headers: this.headers }
    );
  }

  // =====================
  // Recurrence Rules
  // =====================

  recurrenceRuleList(params?: {
    is_active?: boolean;
    account?: number;
    category?: number;
    frequency?: string;
    type?: string;
    search?: string;
  }): Observable<RecurrenceRule[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<RecurrenceRule[]>(
      `${this.baseUrl}/api/finance_manager_planning/recurrence-rules/`,
      { headers: this.headers, params: httpParams }
    );
  }

  recurrenceRuleDetail(id: number): Observable<RecurrenceRule> {
    return this.http.get<RecurrenceRule>(
      `${this.baseUrl}/api/finance_manager_planning/recurrence-rules/${id}/`,
      { headers: this.headers }
    );
  }

  recurrenceRuleCreate(data: RecurrenceRuleCreate): Observable<RecurrenceRule> {
    return this.http.post<RecurrenceRule>(
      `${this.baseUrl}/api/finance_manager_planning/recurrence-rules/`,
      data,
      { headers: this.headers }
    );
  }

  recurrenceRuleUpdate(id: number, data: Partial<RecurrenceRuleCreate>): Observable<RecurrenceRule> {
    return this.http.patch<RecurrenceRule>(
      `${this.baseUrl}/api/finance_manager_planning/recurrence-rules/${id}/`,
      data,
      { headers: this.headers }
    );
  }

  recurrenceRuleDelete(id: number): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/api/finance_manager_planning/recurrence-rules/${id}/`,
      { headers: this.headers }
    );
  }

  recurrenceRuleGenerate(id: number, forDate?: string): Observable<{ message: string; transaction: Transaction }> {
    const body: any = {};
    if (forDate) {
      body.for_date = forDate;
    }
    return this.http.post<{ message: string; transaction: Transaction }>(
      `${this.baseUrl}/api/finance_manager_planning/recurrence-rules/${id}/generate/`,
      body,
      { headers: this.headers }
    );
  }

  // =====================
  // Tax Configurations
  // =====================

  taxConfigList(params?: {
    is_active?: boolean;
    applicable_to?: string;
    current?: boolean;
  }): Observable<TaxConfig[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      });
    }
    return this.http.get<TaxConfig[]>(
      `${this.baseUrl}/api/finance_manager_planning/tax-configs/`,
      { headers: this.headers, params: httpParams }
    );
  }

  taxCalculate(amount: number, taxConfigId?: number): Observable<{
    amount: number;
    total_tax: number;
    net_amount: number;
    breakdown?: any[];
  }> {
    const body: any = { amount };
    if (taxConfigId) {
      body.tax_config_id = taxConfigId;
    }
    return this.http.post<any>(
      `${this.baseUrl}/api/finance_manager_planning/tax-configs/calculate/`,
      body,
      { headers: this.headers }
    );
  }

  // =====================
  // Forecasting
  // =====================

  getForecast(request?: ForecastRequest): Observable<ForecastResult> {
    return this.http.post<ForecastResult>(
      `${this.baseUrl}/api/finance_manager_planning/forecast/`,
      request || { months: 3 },
      { headers: this.headers }
    );
  }

  getForecastGet(months: number = 3, accountIds?: number[]): Observable<ForecastResult> {
    let httpParams = new HttpParams().set('months', String(months));
    if (accountIds && accountIds.length > 0) {
      httpParams = httpParams.set('account_ids', accountIds.join(','));
    }
    return this.http.get<ForecastResult>(
      `${this.baseUrl}/api/finance_manager_planning/forecast/`,
      { headers: this.headers, params: httpParams }
    );
  }
}
