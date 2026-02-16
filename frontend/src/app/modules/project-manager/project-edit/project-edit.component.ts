import { ActivatedRoute, Router } from '@angular/router';
import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { Project } from 'src/app/models/project';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { User } from 'src/app/models/user';
import { ApiService } from 'src/app/services/api/api.services';
import { catchError, of } from 'rxjs';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-project-edit',
  templateUrl: './project-edit.component.html',
  styleUrls: ['./project-edit.component.css']
})
export class ProjectEditComponent implements OnInit {

  project: Project = new Project(null, null, null, null, null, null, null, null, null, null);
  idProject: number = 0;

  durationInSeconds = 5;
  projectForm: UntypedFormGroup | any;

  userList: User[] = [];    // associati
  clientList: User[] = [];  // utenti con permission "user"

  constructor(
    private activatedRoute: ActivatedRoute,
    private apiProject: ProjectApiService,
    private fb: UntypedFormBuilder,
    private api: ApiService,
    private router: Router,
    private _snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.activatedRoute.paramMap.subscribe((params: any) => {
      this.idProject = Number(params.get('id') || 0);
    });

    this.projectForm = this.fb.group({
      id: [''],
      title: ['', [Validators.required, Validators.maxLength(255)]],
      description: [''],
      client: [null, Validators.required],
      insert_date: [{ value: '', disabled: true }],

      contributors: [[]],

      hours_quote_min: [null, Validators.min(0)],
      hours_quote_mid: [null, Validators.min(0)],
      hours_quote_max: [null, Validators.min(0)],
      month_cost_limit: [null, Validators.min(0)],
    });

    this.projectDetailApi();
    this.loadClientsOnly();
    this.userListApi();
  }

  // --- Utility numeriche ---
  private toNumberOrNull(v: any): number | null {
    if (v === null || v === undefined || v === '') return null;
    const n = Number(v);
    return isNaN(n) ? null : n;
  }

  private toFixed2OrNull(v: any): string | null {
    const n = this.toNumberOrNull(v);
    return n === null ? null : n.toFixed(2);
  }

  // --- Caricamento progetto ---
  projectDetailApi() {
    this.apiProject.projectDetail(this.idProject)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API projectDetail', error);
          this.openSnackBar("Errore nel caricamento del progetto.");
          return of(null);
        })
      )
      .subscribe((data: any) => {
        if (!data) return;
        this.project = data;
        this.patchForm();
      });
  }

  patchForm() {
    this.projectForm.patchValue({
      id: this.idProject,
      title: this.project?.title ?? '',
      description: this.project?.description ?? '',
      client: this.project?.client?.id ?? null,
      insert_date: this.project?.insert_date ?? '',

      contributors: Array.isArray(this.project?.contributors) ? this.project.contributors : [],

      hours_quote_min: this.toNumberOrNull(this.project?.hours_quote_min),
      hours_quote_mid: this.toNumberOrNull(this.project?.hours_quote_mid),
      hours_quote_max: this.toNumberOrNull(this.project?.hours_quote_max),
      month_cost_limit: this.toNumberOrNull(this.project?.month_cost_limit),
    });
  }

  // --- Carica lista completa utenti (per associati) ---
  userListApi() {
    this.api.userList()
      .pipe(
        catchError(error => {
          console.error('Errore caricamento utenti', error);
          this.openSnackBar("Errore nel caricamento utenti.");
          return of([]);
        })
      )
      .subscribe((data: any) => {
        this.userList = Array.isArray(data) ? data : [];
      });
  }

  // --- Carica solo utenti con permission "user" (clienti) ---
  loadClientsOnly() {
    this.api.clientList()
      .pipe(
        catchError(error => {
          console.error('Errore caricamento clienti', error);
          this.openSnackBar("Errore nel caricamento clienti.");
          return of([]);
        })
      )
      .subscribe((data: any) => {
        this.clientList = data
      });
  }

  // --- Salvataggio progetto ---
  saveProject() {
    if (this.projectForm.invalid) {
      this.projectForm.markAllAsTouched();
      this.openSnackBar("Controlla i campi evidenziati.");
      return;
    }

    const v = this.projectForm.getRawValue();

    const projectData = {
      id: this.idProject,
      title: v.title,
      description: v.description,
      client: v.client,
      contributors: (v.contributors || []).map((c: any) => c?.id ?? c),

      hours_quote_min: this.toFixed2OrNull(v.hours_quote_min),
      hours_quote_mid: this.toFixed2OrNull(v.hours_quote_mid),
      hours_quote_max: this.toFixed2OrNull(v.hours_quote_max),
      month_cost_limit: this.toFixed2OrNull(v.month_cost_limit),
    };

    this.apiProject.editProject(this.idProject, projectData)
      .pipe(
        catchError(error => {
          console.error('Errore salvataggio progetto', error);
          this.openSnackBar("Errore nel salvataggio.");
          return of(null);
        })
      )
      .subscribe((data: any) => {
        if (data && data.message === 'success') {
          this.openSnackBar("Dati salvati correttamente");
          this.redirectTo('/projects/' + this.idProject);
        } else {
          this.openSnackBar("Errore nel salvataggio dei dati.");
        }
      });
  }

  redirectTo(path: string) {
    this.router.navigate([path]);
  }

  openSnackBar(message: string) {
    this._snackBar.open(message, "", { duration: this.durationInSeconds * 1000 });
  }

  compareFn(a: any, b: any) {
    return a && b ? a.id === b.id : false;
  }
}
