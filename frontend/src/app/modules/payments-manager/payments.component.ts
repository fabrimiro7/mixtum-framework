import { Component, OnInit, ViewChild } from '@angular/core';
import { catchError } from 'rxjs';
import { Router } from '@angular/router';
import { PaymentsApiService } from 'src/app/services/api/payments-api.services';
import { MatSort } from '@angular/material/sort';
import { MatPaginator } from '@angular/material/paginator';
import { MatTableDataSource } from '@angular/material/table';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';
import { DateParser } from 'src/app/util/date_parse';

@Component({
  selector: 'app-payments',
  templateUrl: './payments.component.html',
  styleUrls: ['./payments.component.css']
})
export class PaymentsComponent implements OnInit {

  subscriptions: any[] = []
  payment_toPay: any[] = []
  payment_payed: any[] = []

  subscriptionSource: any = [];

  displayedAdminColumns: string[] = ['title', 'status', 'client', 'project', 'start_date', 'end_date','amount', 'action'];
  displayedClientColumns: string[] = ['title', 'status', 'project', 'start_date', 'end_date','amount', 'action'];

  userType: any = '';

  subscriptionsFilter = [
    { name: 'Tutti', isActive: true },
    { name: 'Attivi', isActive: false},
    { name: 'Scaduti', isActive: false},
  ];

  constructor(
    private apiPayments: PaymentsApiService,
    private router: Router,
    private perm: PermissionService,
    private cookieService: CookieService,
    private dataParser: DateParser,
  ) { }

  @ViewChild(MatSort) sort: MatSort | undefined;
  @ViewChild(MatPaginator) paginator: MatPaginator | undefined;

  ngOnInit(): void {

    var token = this.cookieService.get('token');
    this.userType = this.perm.checkPermission(token);

    this.subscriptionListApi();
    //this.paymentListApi():
  }

  subscriptionListApi() {
    this.apiPayments.subscriptionList()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API subscriptionList:', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.subscriptions = data.data;
        this.subscriptionSource = new MatTableDataSource(data.data);
        this.subscriptionSource.sort = this.sort;
        this.subscriptionSource.paginator = this.paginator;
        this.subscriptionSource.paginator._intl.itemsPerPageLabel = "Abbonamenti per pagina";
        this.subscriptionSource.paginator._intl.nextPageLabel = "Pagina successiva";
        this.subscriptionSource.paginator._intl.previousPageLabel = "Pagina precedente";
      });
  }

  /*paymentListApi() {
    this.apiPayments.paymentList()
        .pipe(
            catchError(error => {
              console.error('Errore nella chiamata API paymentList:', error);
              return [];
            })
        )
        .subscribe((data: any) => {
          this.payment_toPay = data.toPay;
          this.payment_payed = data.payed;
        });
  }*/

  getDisplayedColumns(){
    if (this.userType != 'Utente'){
      return this.displayedAdminColumns;
    }
    else return this.displayedClientColumns;
  }

  truncate(text: string, limit: number){
    const ellipsis = '...';
    return text.length > limit ? text.substring(0, limit) + ellipsis : text;
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

  redirectTo(component: String){
    this.router.navigate([component]);
  }

  getSubscriptionProjects(projects: any[]): string {
    if (!projects || projects.length === 0) {
      return '-';
    }
    if (projects.length === 1) {
      return projects[0].title;
    }
    return `${projects[0].title} +${projects.length - 1}`;
  }

  applyFilters(selectedSubscription: string){

    this.subscriptionsFilter.forEach(filter => {
      filter.isActive = (filter.name === selectedSubscription);
    });

    let filteredSubscriptions;
      switch (selectedSubscription) {
  
        case 'Attivi':
        filteredSubscriptions = this.subscriptions.filter((subscription: any) => subscription.status == 'active');
        this.subscriptionSource = new MatTableDataSource(filteredSubscriptions);
        break;
        
        case 'Scaduti':
          filteredSubscriptions = this.subscriptions.filter((subscription: any) => subscription.status == 'expired');
          this.subscriptionSource = new MatTableDataSource(filteredSubscriptions);
        break; 
  
        default:
          this.subscriptionSource = new MatTableDataSource(this.subscriptions);
      }; 
      this.subscriptionSource.sort = this.sort;
      this.subscriptionSource.paginator = this.paginator;
    }  

  /*    
  subscriptionDetails(idSubscription: any) {
    this.router.navigate(['payments/subscription/' + idSubscription]).then();
  }

  paymentDetails(idPayment: any) {
    this.router.navigate(['/payments/' + idPayment]).then();
  }*/

}
