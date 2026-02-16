import { Component, OnInit } from '@angular/core';
import { PaymentsApiService } from "../../../../services/api/payments-api.services";
import { catchError } from "rxjs";
import { ActivatedRoute, Router } from "@angular/router";
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';
import { DateParser } from 'src/app/util/date_parse';
import { JWTUtils } from 'src/app/util/jwt_validator';

@Component({
  selector: 'app-subscription-detail',
  templateUrl: './subscription-detail.component.html',
  styleUrls: ['./subscription-detail.component.css']
})
export class SubscriptionDetailComponent implements OnInit {
    subscription: any = [];
    subscriptionID = this.actRoute.snapshot.params['id'];
    userType: any = '';
    showEditButton = false;

    constructor(
      public actRoute: ActivatedRoute,
      private auth: PaymentsApiService,
      private router: Router,
      private perm: PermissionService,
      private cookieService: CookieService,
      private dataParser: DateParser,
      private jwt: JWTUtils,
  ) { }

  ngOnInit(): void {
    var token = this.cookieService.get('token');
    this.userType = this.perm.checkPermission(token); 
    const userTypeFromJwt = this.jwt.getUserTypeFromJWT(token)?.toLowerCase();
    this.showEditButton = this.userType === 'SuperAdmin' || userTypeFromJwt === 'associate';
    this.loadSubscriptionDetails();
  }

  loadSubscriptionDetails(){
    this.auth.subscriptionDetails(this.subscriptionID)
        .pipe(
            catchError(error => {
              console.error('Errore nella chiamata API:', error);
              return [];
            })
        )
        .subscribe(
            (data: any) => {
              this.subscription = data.data;
            }
        )
    ;
  }

  //Function to redirect to a component based on what button the user click 
  redirectTo(component: String) {
    this.router.navigate([component]);
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'active':
        return 'status-active';
      case 'expired':
        return 'status-expired';
      default:
        return '';
    }
  } 

  trasformDate(date: string){
    if (date != null){
    return this.dataParser.ISOToNormalDateNoTime(date);
    }
    else return "-";
   }

}
