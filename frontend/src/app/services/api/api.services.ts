import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';

@Injectable()
export class ApiService {

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


  // TESTING API
  testing(): Observable <any> {
    const url: string = this.baseUrl + '/api/testing/element/';
    return this.http.get(url, {headers: this.headers});
  }
  
  // Retriving user list from backend
  userList(): Observable <any> {
    const url: string = this.baseUrl + '/api/v1/users/user/';
    return this.http.get(url, {headers: this.headers});
  }

  clientList(): Observable <any> {
    const url: string = this.baseUrl + '/api/v1/users/client/';
    return this.http.get(url, {headers: this.headers});
  }

  // Retriving worker (user working for the company) list from backend
  workerList(): Observable <any> {
    const url: string = this.baseUrl + '/api/v1/users/user-sa/';
    return this.http.get(url, {headers: this.headers});
  }

  getArticles(): Observable<any> {
    return this.http.get<any>('assets/article.json');
  }
  

}