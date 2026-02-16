import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { catchError, of } from 'rxjs';
import { ApiService } from 'src/app/services/api/api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';

@Component({
  selector: 'app-project-add',
  templateUrl: './project-add.component.html',
  styleUrls: ['./project-add.component.css']
})
export class ProjectAddComponent implements OnInit {

  projectForm: UntypedFormGroup | any;
  userList: any[] = [];
  durationInSeconds = 5;

  constructor(
    private api: ApiService,
    private router: Router,
    private _snackBar: MatSnackBar,
    private fb: UntypedFormBuilder,
    private apiProject: ProjectApiService,
  ) {}

  ngOnInit(): void {
    // Build the form: new fields added and validated
    this.projectForm = this.fb.group({
      title: [{ value: '', disabled: false }, [Validators.required, Validators.maxLength(255)]],
      description: [{ value: '', disabled: false }, [Validators.required]],
      client: [{ value: null, disabled: false }, [Validators.required]],
      contributors: [{ value: [], disabled: false }], // must be an array for multiple select

      // NEW NUMERIC FIELDS
      hours_quote_min: [{ value: null, disabled: false }, [Validators.min(0)]],
      hours_quote_mid: [{ value: null, disabled: false }, [Validators.min(0)]],
      hours_quote_max: [{ value: null, disabled: false }, [Validators.min(0)]],
      month_cost_limit: [{ value: null, disabled: false }, [Validators.min(0)]],
    });

    this.userListApi();
  }

  // Converts to number or null (handles empty strings from number inputs)
  private toNumberOrNull(v: any): number | null {
    if (v === null || v === undefined || v === '') return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }

  // Serializes number to "xx.yy" string or null (matches your API format)
  private toFixed2OrNull(v: any): string | null {
    const n = this.toNumberOrNull(v);
    return n === null ? null : n.toFixed(2);
  }

  userListApi() {
    this.api.userList()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API userList', error);
          this.openSnackBar("Errore nel caricamento utenti.");
          return of([]);
        })
      )
      .subscribe((data: any) => {
        this.userList = Array.isArray(data) ? data : [];
      });
  }

  addProject() {
    if (this.projectForm.invalid) {
      this.projectForm.markAllAsTouched();
      this.openSnackBar("Controlla i campi evidenziati.");
      return;
    }

    const formValue = this.projectForm.getRawValue();

    // Build payload: send IDs for client/contributors, decimals as fixed 2-digit strings
    const projectData = {
      title: formValue.title,
      description: formValue.description,
      client: formValue.client, // it's already an ID from the select
      contributors: (formValue.contributors || []).map((contributor: any) => contributor?.id ?? contributor),

      hours_quote_min: this.toFixed2OrNull(formValue.hours_quote_min),
      hours_quote_mid: this.toFixed2OrNull(formValue.hours_quote_mid),
      hours_quote_max: this.toFixed2OrNull(formValue.hours_quote_max),
      month_cost_limit: this.toFixed2OrNull(formValue.month_cost_limit),
    };

    this.apiProject.projectAdd(projectData)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API projectAdd', error);
          this.openSnackBar("Errore nella creazione del progetto.");
          return of(null);
        })
      )
      .subscribe((data: any) => {
        if (data && data.message === 'success') {
          this.openSnackBar("Progetto aggiunto correttamente");
          this.router.navigate(['projects']);
        } else {
          this.openSnackBar("Errore nella creazione del progetto");
        }
      });
  }

  // Compare function for the multiple select (contributors)
  compareFn(optionOne: any, optionTwo: any): boolean {
    return optionOne && optionTwo ? optionOne.id === optionTwo.id : optionOne === optionTwo;
  }

  redirectTo(component: string) {
    this.router.navigate([component]);
  }

  openSnackBar(message: string) {
    this._snackBar.open(message, "", { duration: this.durationInSeconds * 1000 });
  }
}
