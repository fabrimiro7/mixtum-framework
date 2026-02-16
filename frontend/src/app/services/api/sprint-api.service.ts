import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient, HttpParams } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Phase } from 'src/app/models/phase';

@Injectable()
export class SprintApiService {

  baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;

  private headers: HttpHeaders;

  constructor(
    private http: HttpClient,
    private cookieService: CookieService,
  ) {
    let csfr = this.cookieService.get('csrftoken');
    if (typeof csfr === 'undefined') {
      csfr = '';
    }

    this.headers = new HttpHeaders()
      .set('content-type', 'application/json')
      .set('X-CSRFToken', csfr);
  }

  getProjectPhases(projectId: number): Observable<Phase[]> {
    const url = `${this.baseUrl}/api/sprint_manager/phases/`;
    const params = new HttpParams().set('project', String(projectId));
    return this.http.get<{ data: Phase[] }>(url, { headers: this.headers, params })
      .pipe(map(response => Array.isArray(response?.data) ? response.data : []));
  }

  getAllPhases(): Observable<Phase[]> {
    const url = `${this.baseUrl}/api/sprint_manager/phases/all/`;
    return this.http.get<{ data: Phase[] }>(url, { headers: this.headers })
      .pipe(map(response => Array.isArray(response?.data) ? response.data : []));
  }

  updatePhase(phaseId: number, payload: Partial<Phase>): Observable<Phase> {
    const url = `${this.baseUrl}/api/sprint_manager/phases/${phaseId}/`;
    return this.http.patch<Phase>(url, payload, { headers: this.headers });
  }

  createPhase(projectId: number, payload: Partial<Phase>): Observable<Phase> {
    const url = `${this.baseUrl}/api/sprint_manager/phases/`;
    const body = { ...payload, project: projectId, project_id: projectId };
    return this.http.post<Phase>(url, body, { headers: this.headers });
  }
}
