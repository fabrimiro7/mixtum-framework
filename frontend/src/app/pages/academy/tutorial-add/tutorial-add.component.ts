import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { catchError } from 'rxjs';
import { TutorialApiService } from 'src/app/services/api/academy-api.services';
import { ApiService } from 'src/app/services/api/api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { youtubeLinkToEmbedUrl } from 'src/app/util/youtube-url.util';

@Component({
  selector: 'app-tutorial-add',
  templateUrl: './tutorial-add.component.html',
  styleUrls: ['./tutorial-add.component.css']
})
export class TutorialAddComponent implements OnInit {

  tutorialForm: UntypedFormGroup | any;
  projectList: any = [];
  durationInSeconds = 5;
  workerList: any = [];
  categories: any = [];

  constructor(
    private apiTutorial: TutorialApiService,
    private api: ApiService,
    private router: Router,
    private _snackBar: MatSnackBar,
    private fb: UntypedFormBuilder,
    private apiProject: ProjectApiService,

  ) { }

  ngOnInit(): void {
    this.tutorialForm = this.fb.group({
      title: ['', Validators.required],
      description: ['', Validators.required],
      link: ['', Validators.required],
      project: [[], Validators.required], // Valore iniziale come array vuoto
      duration: [''],
      level: [''],
      author: [null, Validators.required], // Usa null come predefinito
      category: [[], Validators.required],
    });

  this.projectListApi();
  this.workerListApi();
  this.categoriesListApi();
  }

  projectListApi(){
      this.apiProject.projectList()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API projectList', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.projectList = data.data;
      })

  }

  addTutorialApi(){
    const payload = { ...this.tutorialForm.value };
    const embedUrl = youtubeLinkToEmbedUrl(payload.link);
    if (embedUrl) {
      payload.link = embedUrl;
    }
    this.apiTutorial.tutorialAdd(payload)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API tutorialtAdd', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      if (data.message == 'success')
        {
          this.router.navigate(['academy']);
          this.openSnackBar("Tutorial aggiunto correttamente");
        }
        else {
          this.openSnackBar("Errore nella creazione del tutorial");
        }
    })
  }

  workerListApi(){
    this.api.workerList()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API workerList', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.workerList = data;
      })
  }

  categoriesListApi(){
    this.apiTutorial.categoriesList()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API categoriesList', error);
          return [];
        })
      )
      .subscribe((data: any) => {
    
        this.categories = data.data;
      })
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }
  
  openSnackBar(message: string) {
    this._snackBar.open(message, "", {duration: this.durationInSeconds * 1000});
  } 

}
