import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PaymentsManagerRoutingModule } from './payments-manager-routing.module';
import { PaymentAddComponent } from './payments/payment-add/payment-add.component';
import { PaymentEditComponent } from './payments/payment-edit/payment-edit.component';
import { SubscriptionAddComponent } from './subscriptions/subscription-add/subscription-add.component';
import { SubscriptionEditComponent } from './subscriptions/subscription-edit/subscription-edit.component';
import { MatIconModule } from '@angular/material/icon';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { SharedModule } from '../../shared/shared.module';


@NgModule({
  declarations: [
    PaymentAddComponent,
    PaymentEditComponent,
    SubscriptionAddComponent,
    SubscriptionEditComponent
  ],
  imports: [
    CommonModule,
    PaymentsManagerRoutingModule,
    MatIconModule,
    ReactiveFormsModule,
    MatButtonModule,
    SharedModule,
  ]
})
export class PaymentsManagerModule { }
