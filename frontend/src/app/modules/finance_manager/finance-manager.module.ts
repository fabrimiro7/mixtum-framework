import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

// Angular Material
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatMenuModule } from '@angular/material/menu';
import { MatExpansionModule } from '@angular/material/expansion';
import { SharedModule } from '../../shared/shared.module';

// NGX Charts
import { NgxChartsModule } from '@swimlane/ngx-charts';

// Routing
import { FinanceManagerRoutingModule } from './finance-manager-routing.module';

// Components
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

@NgModule({
  declarations: [
    TransactionListComponent,
    TransactionAddComponent,
    TransactionDetailComponent,
    TransactionEditComponent,
    CashflowChartComponent,
    ForecastSimulationComponent,
    RecurringListComponent,
    RecurringEditComponent,
    BankAccountListComponent,
    BankAccountEditComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    FinanceManagerRoutingModule,
    // Material
    MatIconModule,
    MatButtonModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatChipsModule,
    MatTabsModule,
    MatCardModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
    MatDialogModule,
    MatSnackBarModule,
    MatSlideToggleModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatMenuModule,
    MatExpansionModule,
    SharedModule,
    // Charts
    NgxChartsModule
  ]
})
export class FinanceManagerModule { }
