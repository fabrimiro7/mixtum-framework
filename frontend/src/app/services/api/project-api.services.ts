import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';

@Injectable()
export class ProjectApiService {

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
  
  projectList(): Observable <any> {
    const url: string = this.baseUrl + '/api/project_manager/projects/';
    return this.http.get(url, {headers: this.headers});
  }
  //Retriving project details from backend using the project ID
  projectDetail(idProject: any): Observable <any> {
    const url: string = this.baseUrl + '/api/project_manager/projects/' + idProject + '/';
    return this.http.get(url, {headers: this.headers});
  }
  
   //Retriving project list of a user using his ID
  projectsFromUser(idUser: any): Observable <any> {
    const url: string = this.baseUrl + '/api/project_manager/projects-from-user/' + idUser + '/';
    return this.http.get(url, {headers: this.headers});
  }

  projectAdd(newProject: any): Observable <any> {
    const url: string = this.baseUrl + '/api/project_manager/project-post/'
    return this.http.post(url, newProject, {headers: this.headers});
  }

  editProject(idProject: number, project: any): Observable <any> {
    const url: string = this.baseUrl +'/api/project_manager/project-put/'+ idProject + '/';
    return this.http.put(url, project, {headers: this.headers});
  }


}