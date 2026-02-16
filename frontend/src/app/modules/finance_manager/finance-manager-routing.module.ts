import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { isAuthenticatedGuard } from 'src/app/guards/isAuthenticated.guard';
import { IsAdminGuard } from 'src/app/guards/is-admin.guard';

import { TransactionListComponent } from './transaction-list/transaction-list.component';
import { TransactionAddComponent } from './transaction-add/transaction-add.component';
import { TransactionDetailComponent } from './transaction-detail/transaction-detail.component';
import { TransactionEditComponent } from './transaction-edit/transaction-edit.component';
import { CashflowChartComponent } from './cashflow-chart/cashflow-chart.component';
import { ForecastSimulationComponent } from './forecast-simulation/forecast-simulation.component';
import { RecurringListComponent } from './recurring-list/recurring-list.component';
import { RecurringEditComponent } from './recurring-edit/recurring-edit.component';
import { BankAccountListComponent } from './bank-account-list/bank-account-list.component';
import { BankAccountEditComponent } from './bank-account-edit/bank-account-edit.component';

const routes: Routes = [
  { 
    path: '', 
    canActivate: [isAuthenticatedGuard], 
    component: TransactionListComponent, 
    data: { breadcrumb: 'Dashboard Movimenti' }
  },
  { 
    path: 'add', 
    canActivate: [IsAdminGuard], 
    component: TransactionAddComponent, 
    data: { breadcrumb: 'Nuovo Movimento' }
  },
  { 
    path: 'edit/:id', 
    canActivate: [IsAdminGuard], 
    component: TransactionEditComponent, 
    data: { breadcrumb: 'Modifica Movimento' }
  },
  { 
    path: 'chart', 
    canActivate: [isAuthenticatedGuard], 
    component: CashflowChartComponent, 
    data: { breadcrumb: 'Andamento Cashflow' }
  },
  { 
    path: 'simulation', 
    canActivate: [IsAdminGuard], 
    component: ForecastSimulationComponent, 
    data: { breadcrumb: 'Simulazione Previsionale' }
  },
  { 
    path: 'recurring', 
    canActivate: [isAuthenticatedGuard], 
    component: RecurringListComponent, 
    data: { breadcrumb: 'Movimenti Ricorrenti' }
  },
  { 
    path: 'recurring/add', 
    canActivate: [IsAdminGuard], 
    component: RecurringEditComponent, 
    data: { breadcrumb: 'Nuova Regola Ricorrente' }
  },
  { 
    path: 'recurring/edit/:id', 
    canActivate: [IsAdminGuard], 
    component: RecurringEditComponent, 
    data: { breadcrumb: 'Modifica Regola' }
  },
  { 
    path: 'accounts', 
    canActivate: [isAuthenticatedGuard], 
    component: BankAccountListComponent, 
    data: { breadcrumb: 'Banche e Conti' }
  },
  { 
    path: 'accounts/add', 
    canActivate: [IsAdminGuard], 
    component: BankAccountEditComponent, 
    data: { breadcrumb: 'Nuovo Conto' }
  },
  { 
    path: 'accounts/edit/:id', 
    canActivate: [IsAdminGuard], 
    component: BankAccountEditComponent, 
    data: { breadcrumb: 'Modifica Conto' }
  },
  { 
    path: ':id', 
    canActivate: [isAuthenticatedGuard], 
    component: TransactionDetailComponent, 
    data: { breadcrumb: 'Dettaglio Movimento' }
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class FinanceManagerRoutingModule { }
