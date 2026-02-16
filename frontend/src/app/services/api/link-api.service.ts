import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { Observable, of } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { environment } from 'src/environments/django';

@Injectable({
  providedIn: 'root'
})
export class LinkApiService {

  baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;

  private headers: HttpHeaders;
  private contentTypeCache = new Map<string, number>();

  constructor(
    private http: HttpClient,
    private cookieService: CookieService,
  ) {
    let csfr = this.cookieService.get('csrftoken');
    if (typeof (csfr) === 'undefined') {
      csfr = '';
    }

    this.headers = new HttpHeaders()
      .set('content-type', 'application/json')
      .set('X-CSRFToken', csfr);
  }

  private endpoint(path: string = ''): string {
    return `${this.baseUrl}/api/links/links/${path}`;
  }

  list(params?: Record<string, any>): Observable<any> {
    const url = this.endpoint();
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        const value = params[key];
        if (value !== undefined && value !== null && value !== '') {
          httpParams = httpParams.set(key, value);
        }
      });
    }
    return this.http.get(url, { headers: this.headers, params: httpParams });
  }

  create(payload: any): Observable<any> {
    return this.http.post(this.endpoint(), payload, { headers: this.headers });
  }

  update(id: number, payload: any): Observable<any> {
    return this.http.patch(this.endpoint(`${id}/`), payload, { headers: this.headers });
  }

  delete(id: number): Observable<any> {
    return this.http.delete(this.endpoint(`${id}/`), { headers: this.headers });
  }

  getContentTypeId(appLabel: string, model: string): Observable<number> {
    const key = `${appLabel}.${model}`;
    if (this.contentTypeCache.has(key)) {
      return of(this.contentTypeCache.get(key)!);
    }

    const params = new HttpParams()
      .set('app_label', appLabel)
      .set('model', model);

    return this.http.get<{ id: number }>(`${this.baseUrl}/api/links/content-type/`, { headers: this.headers, params })
      .pipe(
        tap(response => this.contentTypeCache.set(key, response.id)),
        map(response => response.id),
      );
  }

}
