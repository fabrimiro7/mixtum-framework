import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { catchError } from 'rxjs';
import { TutorialApiService } from 'src/app/services/api/academy-api.services';

@Component({
  selector: 'app-categories-add',
  templateUrl: './categories-add.component.html',
  styleUrls: ['./categories-add.component.css']
})
export class CategoriesAddComponent implements OnInit {

  categoriesForm: UntypedFormGroup | any;
  categories: any = [];
  durationInSeconds = 5;


  constructor(
    private apiTutorial: TutorialApiService,
    private router: Router,
    private _snackBar: MatSnackBar,
    private fb: UntypedFormBuilder,
  ) { }

  ngOnInit(): void {
    this.categoriesForm = this.fb.group({
      title: ['', Validators.required],
      description: ['', Validators.required],
      parent: [[], Validators.required],
    });

    this.categoriesListApi();
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

  addCategoryAPI(){
    this.apiTutorial.categoryAdd(this.categoriesForm.value)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API categoryAdd', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        if (data.message == 'success')
          {
            this.router.navigate(['academy']);
            this.openSnackBar("Categoria creata correttamente");
          }
          else {
            this.openSnackBar("Errore nella creazione della categoria");
          }
      })
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }
  
  openSnackBar(message: string) {
    this._snackBar.open(message, "", {duration: this.durationInSeconds * 1000});
  } 

}
