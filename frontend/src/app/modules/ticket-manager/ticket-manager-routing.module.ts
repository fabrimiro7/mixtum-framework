import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IsAdminGuard } from 'src/app/guards/is-admin.guard';
import { isAuthenticatedGuard } from 'src/app/guards/isAuthenticated.guard';
import { TicketAddComponent } from './ticket-add/ticket-add.component';
import { TicketDetailsComponent } from './ticket-details/ticket-details.component';
import { TicketEditComponent } from './ticket-edit/ticket-edit.component';
import { TicketListAdminComponent } from './ticket-list-admin/ticket-list-admin.component';
import { TicketsByPeriodComponent } from './tickets-by-period/tickets-by-period.component';
import { TicketListComponent } from './ticket-list/ticket-list.component';

const routes: Routes = [
  { path: '', canActivate: [isAuthenticatedGuard], component: TicketListComponent, data: { breadcrumb: 'Lista Ticket' } },
  { path: 'admin', canActivate: [IsAdminGuard], component: TicketListAdminComponent, data: { breadcrumb: 'Lista Ticket Admin' } },
  { path: 'add', canActivate: [isAuthenticatedGuard], component: TicketAddComponent, data: { breadcrumb: 'Aggiungi Ticket' } },
  { path: ':id', canActivate: [isAuthenticatedGuard], component: TicketDetailsComponent, data: { breadcrumb: 'Dettaglio Ticket' } },
  { path: 'edit/:id', canActivate: [IsAdminGuard], component: TicketEditComponent, data: { breadcrumb: 'Modifica Ticket' }},
  { path: 'list-period/:id', canActivate: [isAuthenticatedGuard], component: TicketsByPeriodComponent, data: { breadcrumb: 'Lista 2 Ticket' } },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class TicketManagerRoutingModule { }
