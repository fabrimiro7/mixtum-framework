import { Component, OnDestroy, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, catchError, of, takeUntil } from 'rxjs';
import { DocumentsApiService } from 'src/app/services/api/documents-api.service';
import { DocumentStatus, DocumentTemplate, DocumentType } from 'src/app/models/document';
import { WorkspaceService } from 'src/app/services/workspace/workspace.service';

@Component({
  selector: 'app-document-create',
  templateUrl: './document-create.component.html',
  styleUrls: ['./document-create.component.css']
})
export class DocumentCreateComponent implements OnInit, OnDestroy {
  form: UntypedFormGroup;
  statuses: DocumentStatus[] = [];
  types: DocumentType[] = [];
  templates: DocumentTemplate[] = [];
  saving = false;
  private destroy$ = new Subject<void>();

  constructor(
    private fb: UntypedFormBuilder,
    private documentsApi: DocumentsApiService,
    private workspaceService: WorkspaceService,
    private router: Router,
    private snackBar: MatSnackBar,
  ) {
    this.form = this.fb.group({
      title: ['', [Validators.required, Validators.maxLength(255)]],
      type_id: [null, Validators.required],
      template_id: [null, Validators.required],
      status_code: [''],
      context: ['{}'],
    });
  }

  ngOnInit(): void {
    this.workspaceService.activeWorkspaceId$
      .pipe(takeUntil(this.destroy$))
      .subscribe((wsId: number | null) => {
        if (!wsId) {
          this.statuses = [];
          this.types = [];
          this.templates = [];
          return;
        }
        this.loadFilters();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadFilters(): void {
    this.documentsApi.listStatuses()
      .pipe(catchError(() => of([] as DocumentStatus[])))
      .subscribe((data: DocumentStatus[]) => {
        this.statuses = data;
        const draft = this.statuses.find(s => s.code === 'draft');
        if (draft) {
          this.form.patchValue({ status_code: draft.code });
        } else if (this.statuses.length > 0) {
          this.form.patchValue({ status_code: this.statuses[0].code });
        }
      });

    this.documentsApi.listTypes()
      .pipe(catchError(() => of([] as DocumentType[])))
      .subscribe((data: DocumentType[]) => {
        this.types = data;
      });

    this.documentsApi.listTemplates()
      .pipe(catchError(() => of([] as DocumentTemplate[])))
      .subscribe((data: DocumentTemplate[]) => {
        this.templates = data;
      });
  }

  createDocument(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    let context: any = {};
    try {
      context = JSON.parse(this.form.value.context || '{}');
    } catch {
      this.openSnackBar('Il JSON del contesto non e\u00e8 valido.');
      return;
    }

    this.saving = true;
    this.documentsApi.createFromTemplate({
      title: this.form.value.title,
      type_id: this.form.value.type_id,
      template_id: this.form.value.template_id,
      status_code: this.form.value.status_code || 'draft',
      context,
    })
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nella creazione del documento.');
          this.saving = false;
          return of(null);
        })
      )
      .subscribe((doc: any) => {
        if (doc?.id) {
          this.router.navigate(['/documents', doc.id]);
        }
        this.saving = false;
      });
  }

  openSnackBar(message: string): void {
    this.snackBar.open(message, '', { duration: 4000 });
  }
}
