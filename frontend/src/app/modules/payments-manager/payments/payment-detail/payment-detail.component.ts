import { Component, OnInit } from '@angular/core';
import { PaymentsApiService } from "../../../../services/api/payments-api.services";
import { catchError } from "rxjs";
import { ActivatedRoute } from "@angular/router";

@Component({
  selector: 'app-payment-detail',
  templateUrl: './payment-detail.component.html',
  styleUrls: ['./payment-detail.component.css']
})
export class PaymentDetailComponent implements OnInit {

  payment: any = [];
  paymentID = this.actRoute.snapshot.params['id'];

    constructor(
        public actRoute: ActivatedRoute,
        private auth: PaymentsApiService,
  ) { }

  ngOnInit(): void {
    this.loadPaymentDetails();
  }

  loadPaymentDetails(){
    this.auth.paymentDetails(this.paymentID)
        .pipe(
            catchError(error => {
              console.error('Errore nella chiamata API:', error);
              return [];
            })
        )
        .subscribe(
            (data: any) => {
              this.payment = data;
            }
        )
    ;
  }

}
