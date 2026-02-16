import { ActivatedRoute, Router } from '@angular/router';
import { Component, OnInit } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { TutorialApiService } from 'src/app/services/api/academy-api.services';
import { catchError } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { DateParser } from 'src/app/util/date_parse';
import { MatSnackBar } from '@angular/material/snack-bar';
import { CdkTextareaAutosize } from '@angular/cdk/text-field';
import { convertUrlsToLinks } from 'src/app/util/safe-html.util';
import { youtubeLinkToEmbedUrl } from 'src/app/util/youtube-url.util';

@Component({
  selector: 'app-tutorial-details',
  templateUrl: './tutorial-details.component.html',
  styleUrls: ['./tutorial-details.component.css']
})
export class TutorialDetailsComponent implements OnInit {

  tutorialDetails: any = [];
  projectDetails: any = []; 
  notaDetails: any = [];
  idTutorial: number = 0;
  idProject: any = [];
  userType: any = '';
  urlTutorial: any = '';
  isModified: boolean = false;
  notaText: string = '';
  durationInSeconds = 5;


  constructor(
    private sanitizer: DomSanitizer,
    private activatedRoute: ActivatedRoute,
    private apiTutorial: TutorialApiService,
    private apiProject: ProjectApiService,
    private perm: PermissionService,
    private cookieService: CookieService,
    private router: Router,
    public dataParser: DateParser,
    private _snackBar: MatSnackBar,
  ) { }

  ngOnInit(): void {
    this.activatedRoute.paramMap
      .subscribe((params: any) => {
        if (params.get('id')) {
          this.idTutorial = Number(params.get('id'));
        }
      });
      var token = this.cookieService.get('token');
      this.userType = this.perm.checkPermission(token);  
    this.loadTutorialDetails();
  }

  getSafeHtml(content: string): SafeHtml {
    const linkedContent = convertUrlsToLinks(content || '');
    return this.sanitizer.bypassSecurityTrustHtml(linkedContent);
  }

  private buildTutorialEmbedUrl(link: string | null | undefined): unknown {
    const embedUrl = youtubeLinkToEmbedUrl(link) || link;
    if (!embedUrl) {
      return null;
    }
    return this.sanitizer.bypassSecurityTrustResourceUrl(embedUrl);
  }

  loadTutorialDetails() {
    this.apiTutorial.tutorialDetail(this.idTutorial)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API tutorialList:', error);
          return [];
        })
      )
      .subscribe(
        (data: any) => {
          this.tutorialDetails = data;
          this.idProject = this.tutorialDetails.projects;
          this.urlTutorial = this.buildTutorialEmbedUrl(this.tutorialDetails.link);
          this.loadProjectDetails();
          this.loadNota();
        });
  }

  loadProjectDetails(){

    // Itera su ogni idProject
    this.idProject.forEach((projectId:number) => {
      this.apiProject.projectDetail(projectId)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API projectDetail per projectId:', projectId, error);
          return []; // Ritorna un valore null per evitare errori successivi
        })
      )
      .subscribe(
        (data:any) => {
          if (data) {
            this.projectDetails.push(data); // Aggiungi i dettagli del progetto all'array
          }
        }
      );
    });
  }

  loadNota(){
    this.apiTutorial.noteDetailByTutorial(this.idTutorial)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API noteDetail', error);
        return[];
      })
    )
    .subscribe(
      (data:any) => {
        this.notaDetails = data.data;
        if(this.notaDetails && this.notaDetails.text != null && this.notaDetails.text != ''){
          this.notaText = this.notaDetails.text;
        }
      }
    )
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }

  onNoteChange(){
    this.isModified = true;
  }

  saveNote(){
    if(this.notaDetails && this.notaDetails.text != null && this.notaDetails.text != ''){ 
    this.notaDetails.text = this.notaText;
    //TO DO: assicurarsi che con un campo di testo aperto non ci siano vulnerabilità utilizzabili//
    this.apiTutorial.noteEdit(this.notaDetails.id, this.notaDetails)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API noteEdit:', error);
        return [];
      })
    )
    .subscribe(
      (data: any) => {
        if (data.message == 'success')
        {
          this.openSnackBar("Dati salvati correttamente");
          this.isModified = false; 

        } else {
          this.openSnackBar("Errore nel salvataggio dei dati. Riprova più tardi.");
        }
      }
    );
  }
  else {
    this.apiTutorial.noteAdd(this.idTutorial, this.notaText)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API noteAdd', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      if (data.message == 'success') {
        this.loadNota();
        this.isModified = false; 
        this.openSnackBar("Dati salvati correttamente");
      } else {
        this.openSnackBar("Errore nel salvataggio dei dati. Riprova più tardi.");
      }
    })
  }
  }

   //snackBar for text notification
 openSnackBar(message: string) {
  this._snackBar.open(message, "", {duration: this.durationInSeconds * 1000});
}


}
