// =====================
// Bank & Account Models
// =====================

export interface Bank {
  id: number;
  name: string;
  abi_code?: string;
  swift_code?: string;
  country?: string;
  website?: string;
  notes?: string;
  is_active: boolean;
  accounts_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Account {
  id: number;
  name: string;
  bank?: Bank | null;
  bank_id?: number | null;
  iban?: string;
  initial_balance: number;
  current_balance?: number;
  currency: string;
  currency_display?: string;
  account_type: AccountType;
  account_type_display?: string;
  description?: string;
  is_active: boolean;
  include_in_totals: boolean;
  color?: string;
  created_at?: string;
  updated_at?: string;
}

export type AccountType = 
  | 'checking'
  | 'savings'
  | 'business'
  | 'cash'
  | 'investment'
  | 'credit_card'
  | 'other';

export interface AccountMinimal {
  id: number;
  name: string;
  bank_name?: string;
  currency: string;
  account_type: AccountType;
}

// =====================
// Category Models
// =====================

export interface Category {
  id: number;
  name: string;
  color: string;
  icon?: string;
  parent?: number | null;
  description?: string;
  transaction_type?: TransactionType | null;
  is_active: boolean;
  sort_order: number;
  full_path?: string;
  depth?: number;
  subcategories_count?: number;
  transaction_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface CategoryMinimal {
  id: number;
  name: string;
  color: string;
  icon?: string;
}

export interface CategoryTree extends CategoryMinimal {
  transaction_type?: TransactionType | null;
  children: CategoryTree[];
}

// =====================
// Transaction Models
// =====================

export type TransactionType = 'income' | 'expense';
export type TransactionStatus = 'pending' | 'scheduled' | 'paid' | 'cancelled';
export type DataSource = 'manual' | 'import_csv' | 'import_excel' | 'import_bank' | 'recurring' | 'api';

export interface Transaction {
  id: number;
  account: AccountMinimal;
  account_id?: number;
  category: CategoryMinimal;
  category_id?: number;
  description: string;
  gross_amount: number;
  net_amount?: number;
  vat_amount?: number;
  signed_amount?: number;
  vat_percentage: number;
  competence_date: string;
  payment_date?: string | null;
  transaction_type: TransactionType;
  transaction_type_display?: string;
  status: TransactionStatus;
  status_display?: string;
  is_hypothetical: boolean;
  data_source: DataSource;
  data_source_display?: string;
  external_reference?: string;
  notes?: string;
  recurring_rule?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface TransactionCreate {
  account: number;
  category: number;
  description: string;
  gross_amount: number;
  vat_percentage?: number;
  competence_date: string;
  payment_date?: string | null;
  transaction_type: TransactionType;
  status?: TransactionStatus;
  is_hypothetical?: boolean;
  external_reference?: string;
  notes?: string;
}

export interface TransactionListParams {
  page?: number;
  page_size?: number;
  account?: number;
  category?: number;
  type?: TransactionType;
  status?: TransactionStatus;
  is_hypothetical?: boolean;
  from?: string;
  to?: string;
  period?: 'this_month' | 'last_month' | 'this_year' | 'last_3_months';
  overdue?: boolean;
  search?: string;
  ordering?: string;
}

export interface TransactionListResponse {
  count: number;
  next?: string | null;
  previous?: string | null;
  results: Transaction[];
}

// =====================
// Cashflow & Analytics
// =====================

export interface CashflowPeriod {
  period: string;
  period_start: string;
  period_end: string;
  total_income: number;
  total_expenses: number;
  net_cashflow: number;
  transaction_count: number;
}

export interface CashflowSummaryResponse {
  granularity: 'month' | 'year';
  results: CashflowPeriod[];
}

export interface CategoryBreakdownItem {
  category_id: number;
  category_name: string;
  category_color: string;
  total: number;
  count: number;
  percentage: number;
}

export interface CategoryBreakdownResponse {
  grand_total: number;
  breakdown: CategoryBreakdownItem[];
}

// =====================
// Recurrence Rules
// =====================

export type Frequency = 
  | 'daily'
  | 'weekly'
  | 'biweekly'
  | 'monthly'
  | 'bimonthly'
  | 'quarterly'
  | 'semiannual'
  | 'annual';

export interface RecurrenceRule {
  id: number;
  name: string;
  template_transaction?: number | null;
  account: AccountMinimal;
  account_id?: number;
  category: CategoryMinimal;
  category_id?: number;
  description: string;
  gross_amount: number;
  vat_percentage: number;
  transaction_type: TransactionType;
  transaction_type_display?: string;
  frequency: Frequency;
  frequency_display?: string;
  day_of_month?: number | null;
  day_of_week?: number | null;
  start_date: string;
  end_date?: string | null;
  last_generated_date?: string | null;
  is_active: boolean;
  generate_as_hypothetical: boolean;
  notes?: string;
  next_occurrence?: string | null;
  generated_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface RecurrenceRuleCreate {
  name: string;
  account: number;
  category: number;
  description: string;
  gross_amount: number;
  vat_percentage?: number;
  transaction_type: TransactionType;
  frequency: Frequency;
  day_of_month?: number | null;
  day_of_week?: number | null;
  start_date: string;
  end_date?: string | null;
  is_active?: boolean;
  generate_as_hypothetical?: boolean;
  notes?: string;
}

// =====================
// Budget
// =====================

export type BudgetPeriod = 'monthly' | 'quarterly' | 'semiannual' | 'annual';

export interface Budget {
  id: number;
  category: CategoryMinimal;
  category_id?: number;
  account?: AccountMinimal | null;
  account_id?: number | null;
  target_value: number;
  period: BudgetPeriod;
  period_display?: string;
  alert_threshold: number;
  start_date: string;
  end_date?: string | null;
  is_active: boolean;
  notes?: string;
  current_usage?: number;
  current_percentage?: number;
  is_over_budget?: boolean;
  is_near_limit?: boolean;
  created_at?: string;
  updated_at?: string;
}

// =====================
// Tax Configuration
// =====================

export type TaxApplicableTo = 'income' | 'expense' | 'all' | 'category';

export interface TaxConfig {
  id: number;
  name: string;
  percentage: number;
  applicable_to: TaxApplicableTo;
  applicable_to_display?: string;
  applicable_categories?: CategoryMinimal[];
  threshold_amount?: number | null;
  is_progressive: boolean;
  description?: string;
  valid_from: string;
  valid_until?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// =====================
// Forecasting
// =====================

export interface ForecastPeriod {
  period_start: string;
  period_end: string;
  period_label: string;
  projected_income: number;
  projected_expenses: number;
  net_cashflow: number;
  cumulative_balance: number;
  hypothetical_income: number;
  hypothetical_expenses: number;
}

export interface ForecastResult {
  start_date: string;
  end_date: string;
  months: number;
  starting_balance: number;
  ending_balance: number;
  total_projected_income: number;
  total_projected_expenses: number;
  net_change: number;
  periods: ForecastPeriod[];
  warnings: string[];
}

export interface ForecastRequest {
  months?: number;
  account_ids?: number[];
  include_hypothetical?: boolean;
  include_recurring?: boolean;
  use_historical_averages?: boolean;
  historical_months?: number;
}

// =====================
// Aggregate Balance
// =====================

export interface AggregateBalanceItem {
  id: number;
  name: string;
  bank_name?: string;
  currency: string;
  account_type: AccountType;
  balance: number;
}

export interface AggregateBalanceResponse {
  total_balance: number;
  currency: string;
  accounts_count: number;
  accounts: AggregateBalanceItem[];
}

// =====================
// Import
// =====================

export interface ImportResult {
  success: boolean;
  imported: number;
  skipped: number;
  duplicates?: number;
  errors: Array<{
    row: number;
    error: string;
    data?: any;
  }>;
}
