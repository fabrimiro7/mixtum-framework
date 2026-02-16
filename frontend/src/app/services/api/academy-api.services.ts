import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { environment } from 'src/environments/django';
import { Observable } from 'rxjs';

@Injectable()
export class TutorialApiService {

  baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;

    /**
     *  HTTP Headers for API Calls
     */
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

  tutorialList(): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/tutorial/';
    return this.http.get(url, {headers: this.headers});
  }

  tutorialDetail(idTutorial: number): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/tutorial-detail/' + idTutorial + '/';
    return this.http.get(url, {headers: this.headers});
  }

  tutorialAdd( newTutorial: any ): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/tutorial-post/';
    return this.http.post(url, newTutorial, {headers: this.headers});
  }

  tutorialEdit (idTutorial: any, tutorial: any): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/tutorial-put/' + idTutorial + '/';
    return this.http.put(url, tutorial, {headers: this.headers});
  }

  noteDetailByTutorial(idTutorial: number): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/notes/by-tutorial/' + idTutorial + '/';
    return this.http.get(url, {headers: this.headers});
  }

  noteAdd (tutorial_id: number, text: any): Observable <any>  {
    const url: string = this.baseUrl + '/api/academy_manager/notes/add/';
    return this.http.post(url, {tutorial_id,text}, {headers: this.headers});
  }

  noteEdit (idNota: any, nota: any): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/notes/' + idNota + '/';
    return this.http.put(url, nota, {headers: this.headers});
  }

  categoriesList(): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/categories/';
    return this.http.get(url, {headers: this.headers});
  }

  categoryAdd( newCategory: any): Observable <any> {
    const url: string = this.baseUrl + '/api/academy_manager/category-create/';
    return this.http.post(url, newCategory, {headers: this.headers});
  }


}
