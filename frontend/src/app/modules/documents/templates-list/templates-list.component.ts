import { Component, OnDestroy, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, catchError, of, takeUntil } from 'rxjs';

import { DocumentsApiService } from 'src/app/services/api/documents-api.service';
import { DocumentTemplate } from 'src/app/models/document';
import { WorkspaceService } from 'src/app/services/workspace/workspace.service';

@Component({
  selector: 'app-templates-list',
  templateUrl: './templates-list.component.html',
  styleUrls: ['./templates-list.component.css']
})
export class TemplatesListComponent implements OnInit, OnDestroy {
  templates: DocumentTemplate[] = [];
  form: UntypedFormGroup;
  loading = false;
  private destroy$ = new Subject<void>();

  constructor(
    private documentsApi: DocumentsApiService,
    private fb: UntypedFormBuilder,
    private workspaceService: WorkspaceService,
    private router: Router,
    private snackBar: MatSnackBar,
  ) {
    this.form = this.fb.group({
      title: ['', [Validators.required, Validators.maxLength(255)]],
      description: [''],
    });
  }

  ngOnInit(): void {
    this.workspaceService.activeWorkspaceId$
      .pipe(takeUntil(this.destroy$))
      .subscribe((wsId: number | null) => {
        if (!wsId) {
          this.templates = [];
          return;
        }
        this.loadTemplates();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadTemplates(): void {
    this.loading = true;
    this.documentsApi.listTemplates()
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel caricamento template.');
          this.loading = false;
          return of([] as DocumentTemplate[]);
        })
      )
      .subscribe((data: DocumentTemplate[]) => {
        this.templates = data;
        this.loading = false;
      });
  }

  createTemplate(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.documentsApi.createTemplate(this.form.value)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nella creazione template.');
          return of(null);
        })
      )
      .subscribe((tpl: DocumentTemplate | null) => {
        if (!tpl) {
          return;
        }
        this.form.reset();
        this.loadTemplates();
      });
  }

  openTemplate(tpl: DocumentTemplate): void {
    this.router.navigate(['/documents/templates', tpl.id]);
  }

  deleteTemplate(tpl: DocumentTemplate): void {
    this.documentsApi.deleteTemplate(tpl.id)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nella rimozione template.');
          return of(null);
        })
      )
      .subscribe(() => {
        this.loadTemplates();
      });
  }

  openSnackBar(message: string): void {
    this.snackBar.open(message, '', { duration: 4000 });
  }
}
