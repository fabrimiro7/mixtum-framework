import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError } from 'rxjs';
import { ApiService } from 'src/app/services/api/api.services';
import { PaymentsApiService } from 'src/app/services/api/payments-api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { DateParser } from 'src/app/util/date_parse';

@Component({
  selector: 'app-subscription-edit',
  templateUrl: './subscription-edit.component.html',
  styleUrls: ['./subscription-edit.component.css']
})
export class SubscriptionEditComponent implements OnInit {

  subscriptionForm: UntypedFormGroup | any;
  customerList: any = [];
  projectList: any = []; //occhio una volta scelto il cliente devo per scegliere solo tra progetti associati a quel cliente e viceversa
  durationInSeconds = 5;
  idSubscription: any;
  subscription: any;

  constructor(
    private apiPayment: PaymentsApiService,
    private apiProject: ProjectApiService,
    private api: ApiService,
    private router: Router,
    private _snackBar: MatSnackBar,
    private fb: UntypedFormBuilder,
    private activatedRoute: ActivatedRoute,
    public dataParser: DateParser,
  ) { }

  ngOnInit(): void {
    this.activatedRoute.paramMap
    .subscribe((params: any) => {
      if (params.get('id')) {
        this.idSubscription = Number(params.get('id'));
            }
    });

    this.subscriptionForm = this.fb.group({
      id: [{value:'', disabled: false}],
      title: ['', Validators.required],
      description: ['', Validators.required], 
      customer: ['', Validators.required], 
      project: [[], Validators.required], 
      start_date: ['', Validators.required], 
      end_date: ['', Validators.required], 
      amount: ['', Validators.required],  
      status: ['', Validators.required], 
    })

    this.subscriptionDetailApi();
    this.customerListApi();
    this.projectListApi();
  }

  subscriptionDetailApi(){
    this.apiPayment.subscriptionDetails(this.idSubscription)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API subscriptionDetails:', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      this.subscription = data.data;
      this.patchForm();
    })

  }

  patchForm(){
    this.subscriptionForm.patchValue({
      id: this.idSubscription,
      title: this.subscription.title,
      description: this.subscription.description,
      customer: this.subscription.customer.id,
      project: this.subscription.project.map((p: any) => p.id),
      start_date: this.subscription.start_date,
      end_date: this.subscription.end_date,
      amount: this.subscription.amount,
      status: this.subscription.status
    })
  }

  customerListApi(){
    this.api.userList()
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API userList', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      this.customerList = data;
    })
  }

  projectListApi(){
    this.apiProject.projectList()
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API projectList', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      this.projectList = data.data;
    })

  }

  saveSubscription(){
    this.apiPayment.subscriptionEdit(this.idSubscription, this.subscriptionForm.value)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API subscriptionEdit', error)
        return [];
      })
    )
    .subscribe(
      (data: any) => {
        if (data.message == 'success')
        {
          this.openSnackBar("Dati salvati correttamente");
          this.redirectTo('/payments/');

        } else {
          this.openSnackBar("Errore nel salvataggio dei dati. Riprova più tardi.");
        }
      }
      );
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }
  openSnackBar(message: string) {
    this._snackBar.open(message, "", {duration: this.durationInSeconds * 1000});
  } 
}
