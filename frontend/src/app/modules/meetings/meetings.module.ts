import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MeetingsRoutingModule } from './meetings-routing.module';
import { SharedModule } from '../../shared/shared.module';


@NgModule({
  declarations: [
  ],
  imports: [
    CommonModule,
    MeetingsRoutingModule,
    MatIconModule,
    ReactiveFormsModule,
    MatButtonModule,
    SharedModule,
  ]
})
export class PaymentsManagerModule { }
