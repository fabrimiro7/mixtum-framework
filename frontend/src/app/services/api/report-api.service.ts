import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Report } from 'src/app/models/report';

@Injectable()
export class ReportApiService {

  baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;

  private headers: HttpHeaders;

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
  }

  getProjectReports(projectId: number): Observable<Report[]> {
    const url = `${this.baseUrl}/api/report_manager/reports/project/${projectId}/`;
    return this.http.get<{ data: Report[] }>(url, { headers: this.headers })
      .pipe(map(response => Array.isArray(response?.data) ? response.data : []));
  }

  createReport(report: Partial<Report>): Observable<Report> {
    const url = `${this.baseUrl}/api/report_manager/reports/`;
    return this.http.post<{ data: Report }>(url, report, { headers: this.headers })
      .pipe(map(response => response.data));
  }

  updateReport(reportId: number, report: Partial<Report>): Observable<Report> {
    const url = `${this.baseUrl}/api/report_manager/reports/${reportId}/`;
    return this.http.put<{ data: Report }>(url, report, { headers: this.headers })
      .pipe(map(response => response.data));
  }

  deleteReport(reportId: number): Observable<any> {
    const url = `${this.baseUrl}/api/report_manager/reports/${reportId}/`;
    return this.http.delete(url, { headers: this.headers });
  }
}
