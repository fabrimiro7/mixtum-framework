import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';


@Injectable()
export class AuthService {
                                       
  baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;


  /**
   *  HTTP Headers for API Calls
   */
  private headersForFile: HttpHeaders;
  private headers: HttpHeaders;
  private headersDefault: HttpHeaders;

  /**
   * JWT var 
   */
  refreshToken = "";
  accessToken = "";
  isAuthenticated = false;

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

  /**
   *  API AUTH
   */

  /**
   * Login API 
   * Simple login api 
   * @param user 
   * @returns access token and refresh token (JWT) from Django Rest Framework
   */
  login(user: any): Promise <any> {
    const url: string = this.baseUrl + '/api/v1/users/login/';
    return this.http.post(url, user, {headers: this.headers}).toPromise();
  }
  /**
   * Refresh JWT Token API
   * when interceptor detect 403 http error
   * @returns refresh token (JWT) from Django Rest Framework
   */
  refresh() {
    const url: string = this.baseUrl + '/api/v1/users/refresh/';
    this.refreshToken = this.cookieService.get('refresh_token');
    return this.http.post(url, {reftok: this.refreshToken},  {headers: this.headersDefault});
  }
  /**
   * Register API
   * Register new user in Django Rest Framework
   * @param newUser 
   * @returns id of new user register
   */
  registerUser(newUser: any): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/register/';
    return this.http.post(url, newUser, {headers: this.headersDefault});
  }
  /**
   * Create User API
   * Register new user in Django Rest Framework by Admin
   * @param newUser 
   * @returns id of new user register
   */
  createUser(newUser: any): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/add-user/';
    return this.http.post(url, newUser, {headers: this.headersDefault});
  }
  /**
   * List User API
   * Show a list of all user registered
   * @returns list of all user
   */
  listUser(): Observable<any> {
    var url: string = this.baseUrl + '/api/v1/users/user/';
    return this.http.get(url, {headers: this.headersDefault});
  }
  /**
   * 
   * @param idUser 
   * @returns 
   */
  detailUser(idUser: any): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/' + idUser + '/user-detail/';
    return this.http.get(url, {headers: this.headers});
  }
  editUser(idUser: any, user: any): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/' + idUser + '/user-detail/';
    return this.http.put(url, user, {headers: this.headers});
  }
  editAvatarUser(idUser: any, avatar: any): Observable<any> {
    console.log("sono qua")
    const url: string = this.baseUrl + '/api/v1/users/' + idUser + '/user-avatar/';
    return this.http.put(url, avatar, {headers: this.headersForFile});
  }
  deleteUser(idUser: any): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/' + idUser + '/user-detail/';
    return this.http.delete(url, {headers: this.headers});
  }
  logout(): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/logout/';
    return this.http.post(url, '', {headers: this.headers});
  }
  sendEmail(newPassword: any): Observable<any> {
    const url = this.baseUrl + '/api/v1/users/reset/';
    return this.http.post(url, newPassword, {headers: this.headers});
  }
  resetPassword(newPassword: any): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/reset-complete/' + newPassword.id + '/' + newPassword.token + '/';
    return this.http.post(url, newPassword, {headers: this.headers});
  }
  editUserAvatar(idUser: any, avatar: any): Observable<any> {
    const url: string = this.baseUrl + '/api/v1/users/' + idUser + '/user-avatar/';
    return this.http.put(url, avatar, {headers: this.headersForFile});
  }

}
