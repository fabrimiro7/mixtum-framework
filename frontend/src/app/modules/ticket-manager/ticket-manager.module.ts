import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { TicketManagerRoutingModule } from './ticket-manager-routing.module';
import { TicketsByPeriodComponent } from './tickets-by-period/tickets-by-period.component';
import { TicketListComponent } from './ticket-list/ticket-list.component';
import { TicketListAdminComponent } from './ticket-list-admin/ticket-list-admin.component';
import { TicketPaymentsDashboardComponent } from './ticket-payments-dashboard/ticket-payments-dashboard.component';


@NgModule({
  declarations: [

  ],
  imports: [
    CommonModule,
    TicketManagerRoutingModule
  ]
})
export class TicketManagerModule { }
