import { Component, OnInit } from '@angular/core';
import { TutorialApiService } from "../../../services/api/academy-api.services";
import { catchError } from "rxjs";
import { Router } from "@angular/router";
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';

@Component({
  selector: 'app-academy',
  templateUrl: './academy.component.html',
  styleUrls: ['./academy.component.css']
})
export class AcademyComponent implements OnInit {

  tutorials: any = [];
  userType: any = '';

  constructor(
      private auth: TutorialApiService,
      private router: Router,
      private perm: PermissionService,
      private cookieService: CookieService,
  ) { }

  ngOnInit(): void {
    var token = this.cookieService.get('token');
    this.userType = this.perm.checkPermission(token);
    this.loadTutorial();
  }

  loadTutorial(){
      this.auth.tutorialList()
          .pipe(
              catchError(error => {
                  console.error('Errore nella chiamata API tutorialList:', error);
                  return [];
              })
          )
          .subscribe(
              (data: any) => {
                  this.tutorials = data;
              }
          )
      ;
  }

  getMiniature(id: number) {
    const tutorial = this.tutorials.find((t: any) => t.id === id);  // Trova il tutorial con l'ID corrispondente
  
    if (!tutorial) {
      console.error(`Nessun tutorial trovato con l'ID ${id}`);
      return '';  // Restituisci un valore di fallback se il tutorial non esiste
    }
  
    const link = tutorial.link;
  
    if (!link) {
      console.error(`Nessun link trovato per il tutorial con l'ID ${id}`);
      return '';  // Restituisci un valore di fallback se il link non esiste
    }
  
    const videoId = this.extractVideoId(link);
    return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
  }

  extractVideoId(url: string) {
    if (!url) {
      return '';  // Restituisci un valore di fallback se l'URL è vuoto o indefinito
    }
  
    try {
      const urlSplit1 = url.split('/');
      const urlSplit2 = urlSplit1[4].split('?');
      return urlSplit2[0];
    } catch (error) {
      console.error('Errore nell\'estrarre l\'ID del video:', error);
      return '';  // Restituisci un valore di fallback in caso di errore
    }
  }
  

  redirectTo(component: String){
    this.router.navigate([component]);
 }

 truncate(text: string, limit: number){
    const ellipsis = '...';
    return text.length > limit ? text.substring(0, limit) + ellipsis : text;
   }

}
