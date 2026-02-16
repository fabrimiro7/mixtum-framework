import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { catchError } from 'rxjs';
import { ApiService } from 'src/app/services/api/api.services';
import { PaymentsApiService } from 'src/app/services/api/payments-api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';


@Component({
  selector: 'app-subscription-add',
  templateUrl: './subscription-add.component.html',
  styleUrls: ['./subscription-add.component.css']
})
export class SubscriptionAddComponent implements OnInit {

  subscriptionForm: UntypedFormGroup | any;
  customerList: any = [];
  projectList: any = []; //occhio una volta scelto il cliente devo per scegliere solo tra progetti associati a quel cliente e viceversa
  durationInSeconds = 5;


  constructor(
    private apiPayment: PaymentsApiService,
    private apiProject: ProjectApiService,
    private api: ApiService,
    private router: Router,
    private _snackBar: MatSnackBar,
    private fb: UntypedFormBuilder,
  ) { }

  ngOnInit(): void {
    this.subscriptionForm = this.fb.group({
      title: ['', Validators.required],
      description: ['', Validators.required], 
      customer: ['', Validators.required], 
      project: [[], Validators.required], 
      start_date: ['', Validators.required], 
      end_date: ['', Validators.required], 
      amount: ['', Validators.required],  
      status: ['', Validators.required], 
    })

    this.customerListApi();
    this.projectListApi();

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

  addSubscriptionsApi(){
    this.apiPayment.subscriptionAdd(this.subscriptionForm.value)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API subscriptiontAdd', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      if (data.message == 'success')
        {
          this.router.navigate(['payments']);
          this.openSnackBar("Abbonamento aggiunto correttamente");
        }
        else {
          this.openSnackBar("Errore nella creazione dell'abbonamento");
        }
    })
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }

  openSnackBar(message: string) {
    this._snackBar.open(message, "", {duration: this.durationInSeconds * 1000});
  } 

}
