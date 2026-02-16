import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';

@Injectable()
export class PaymentsApiService {

  baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;

    /**
     *  HTTP Headers for API Calls
     */
    private headersForFile: HttpHeaders;
    private headers: HttpHeaders;
    private headersDefault: HttpHeaders;

    constructor(
        private http: HttpClient,
        private cookieService: CookieService,
      ) {
        
    let csfr = this.cookieService.get('csrftoken');
    if (typeof(csfr) === 'undefined') {
      csfr = '';
    }

    this.headers = new HttpHeaders()
      .set('content-type', 'application/json')
      .set('X-CSRFToken', csfr);

    this.headersForFile = new HttpHeaders()
      .set('X-CSRFToken', csfr);

    this.headersDefault = new HttpHeaders()
      .set('content-type', 'application/json')
  }

  subscriptionList(): Observable <any> {
    const url: string = this.baseUrl + '/api/payments_manager/subscriptions-list/';
    return this.http.get(url, {headers: this.headers});
  }

  subscriptionDetails(idSubscription: any): Observable <any> {
    const url: string = this.baseUrl + '/api/payments_manager/subscriptions/' + idSubscription + '/';
    return this.http.get(url, {headers: this.headers});
  }

  subscriptionAdd(newSubscription: any): Observable <any> {
    const url: string = this.baseUrl + '/api/payments_manager/subscriptions-add/';
    return this.http.post(url, newSubscription, {headers: this.headers});
  }

  subscriptionEdit(idSubscription: number, subscription: any): Observable <any> {
    const url: string = this.baseUrl +'/api/payments_manager/subscription-put/'+ idSubscription + '/';
    return this.http.put(url, subscription, {headers: this.headers});
  }

  paymentList(): Observable <any> {
    const url: string = this.baseUrl + '/api/payments_manager/subscriptions/';
    return this.http.get(url, {headers: this.headers});
  }

  paymentDetails(idPayment: any): Observable <any> {
    const url: string = this.baseUrl + '/api/payments_manager/subscriptions/' + idPayment + '/';
    return this.http.get(url, {headers: this.headers});
  }
}
