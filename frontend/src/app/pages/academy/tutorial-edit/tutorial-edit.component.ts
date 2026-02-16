import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError } from 'rxjs';
import { Project } from 'src/app/models/project';
import { Tutorial } from 'src/app/models/tutorial';
import { TutorialApiService } from 'src/app/services/api/academy-api.services';
import { ApiService } from 'src/app/services/api/api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { youtubeLinkToEmbedUrl } from 'src/app/util/youtube-url.util';


@Component({
  selector: 'app-tutorial-edit',
  templateUrl: './tutorial-edit.component.html',
  styleUrls: ['./tutorial-edit.component.css']
})
export class TutorialEditComponent implements OnInit {

  tutorial: Tutorial = new Tutorial (null,null,null,null,null, null, null, null, null);
  idTutorial: number = 0;
  durationInSeconds = 5;
  tutorialForm: UntypedFormGroup | any;
  projectList: Project[] = [];
  categories: any = [];
  workerList: any = [];

  constructor(
    private activatedRoute: ActivatedRoute,
    private apiTutorial: TutorialApiService,
    private api: ApiService,
    private fb: UntypedFormBuilder,
    private apiProject: ProjectApiService,
    private router: Router,
    private _snackBar: MatSnackBar,
  ) { }

  ngOnInit(): void {
    this.activatedRoute.paramMap
    .subscribe((params: any) => {
      if (params.get('id')) {
        this.idTutorial = Number(params.get('id'));
      }
    });

      this.tutorialForm = this.fb.group({
      title: [{value:'', disabled: false}, Validators.required],
      description: [{value:'', disabled: false}, Validators.required],
      link: [{value:'', disabled: false}, Validators.required],
      project: [[], Validators.required],
      duration: [{value:'', disable: false}],
      level: [{value:'', disable: false}],
      author: [{value:'', disable: false}, Validators.required],
      category: [[], Validators.required],
    });
    
    this.projectListApi();
    this.tutorialDetailApi();
    this.workerListApi();
    this.categoriesListApi();
  }

  tutorialDetailApi(){
    this.apiTutorial.tutorialDetail(this.idTutorial)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API tutorialDetail', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      this.tutorial = data;
      this.patchForm();
    })
  }

  patchForm(){
    this.tutorialForm.patchValue({
      //id: this.idTutorial,
      title: this.tutorial.title,
      description: this.tutorial.description,
      link: this.tutorial.link,
      project: this.tutorial.projects,
      duration: this.tutorial.duration,
      level: this.tutorial.level,
      author: this.tutorial.author.id,
      category: Array.isArray(this.tutorial.category)
      ? this.tutorial.category.map((category: any) => category.id)
      : [],
    })

  }

  projectListApi(){
    this.apiProject.projectList()
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API projectList', error)
        return [];
      })
    )
    .subscribe((data: any) => {
      this.projectList = data.data;
    });
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

  saveTutorial(){
    const payload = { ...this.tutorialForm.value };
    const embedUrl = youtubeLinkToEmbedUrl(payload.link);
    if (embedUrl) {
      payload.link = embedUrl;
    }
    this.apiTutorial.tutorialEdit(this.idTutorial, payload)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API tutorialEdit', error)
        return [];
      })
    )
    .subscribe(
      (data: any) => {
        if (data.message == 'success')
          {
            this.openSnackBar("Dati salvati correttamente");
            this.redirectTo('/academy/');

          } else {
            this.openSnackBar("Errore nel salvataggio dei dati. Riprova più tardi.");
          }
      }
    )
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
