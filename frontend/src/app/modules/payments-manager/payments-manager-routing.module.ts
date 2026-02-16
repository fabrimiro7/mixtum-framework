import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { isAuthenticatedGuard } from 'src/app/guards/isAuthenticated.guard';
import { PaymentDetailComponent } from './payments/payment-detail/payment-detail.component';
import { PaymentsComponent } from './payments.component';
import { SubscriptionDetailComponent } from './subscriptions/subscription-detail/subscription-detail.component';
import { SubscriptionAddComponent } from './subscriptions/subscription-add/subscription-add.component';
import { IsAdminGuard } from 'src/app/guards/is-admin.guard';
import { SubscriptionEditComponent } from './subscriptions/subscription-edit/subscription-edit.component';

const routes: Routes = [
  { path: '', canActivate: [isAuthenticatedGuard], component: PaymentsComponent, data: { breadcrumb: 'Dashboard Pagamenti' }},
  { path: 'subscription/add', canActivate: [IsAdminGuard], component: SubscriptionAddComponent, data: { breadcrumb: 'Aggiungi Abbonamento' }},
  { path: 'subscription/edit/:id', canActivate: [IsAdminGuard], component: SubscriptionEditComponent, data: { breadcrumb: 'Modifica Abbonamento' }},
  { path: 'subscription/:id', canActivate: [isAuthenticatedGuard], component: SubscriptionDetailComponent, data: { breadcrumb: 'Dettagli Abbonamento' }},
  { path: ':id', canActivate: [isAuthenticatedGuard], component: PaymentDetailComponent, data: { breadcrumb: 'Dettaglio Pagamento' }},
  
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PaymentsManagerRoutingModule { }
