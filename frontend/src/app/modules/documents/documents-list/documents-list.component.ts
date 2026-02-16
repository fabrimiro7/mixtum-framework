import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, catchError, of, takeUntil } from 'rxjs';
import { DocumentsApiService } from 'src/app/services/api/documents-api.service';
import { WorkspaceService } from 'src/app/services/workspace/workspace.service';
import { Document, DocumentStatus, DocumentType } from 'src/app/models/document';

@Component({
  selector: 'app-documents-list',
  templateUrl: './documents-list.component.html',
  styleUrls: ['./documents-list.component.css']
})
export class DocumentsListComponent implements OnInit, OnDestroy {
  documents: Document[] = [];
  statuses: DocumentStatus[] = [];
  types: DocumentType[] = [];
  statusMap = new Map<number, string>();
  typeMap = new Map<number, string>();
  selectedStatus: number | null = null;
  selectedType: number | null = null;
  loading = false;
  private destroy$ = new Subject<void>();

  constructor(
    private documentsApi: DocumentsApiService,
    private workspaceService: WorkspaceService,
    private router: Router,
    private snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.workspaceService.activeWorkspaceId$
      .pipe(takeUntil(this.destroy$))
      .subscribe((wsId: number | null) => {
        if (!wsId) {
          this.documents = [];
          this.statuses = [];
          this.types = [];
          return;
        }
        this.loadFilters();
        this.loadDocuments();
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
        this.statusMap = new Map(data.map(status => [status.id, status.title]));
      });

    this.documentsApi.listTypes()
      .pipe(catchError(() => of([] as DocumentType[])))
      .subscribe((data: DocumentType[]) => {
        this.types = data;
        this.typeMap = new Map(data.map(type => [type.id, type.title]));
      });
  }

  loadDocuments(): void {
    this.loading = true;
    this.documentsApi.listDocuments({
      status: this.selectedStatus ?? undefined,
      type: this.selectedType ?? undefined,
    })
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel caricamento documenti.');
          return of([] as Document[]);
        })
      )
      .subscribe((data: Document[]) => {
        this.documents = data;
        this.loading = false;
      });
  }

  resetFilters(): void {
    this.selectedStatus = null;
    this.selectedType = null;
    this.loadDocuments();
  }

  goToDocument(doc: Document): void {
    this.router.navigate(['/documents', doc.id]);
  }

  goToCreate(): void {
    this.router.navigate(['/documents/new']);
  }

  getTypeLabel(typeId: number | null | undefined): string {
    if (typeId === null || typeId === undefined) {
      return '-';
    }
    return this.typeMap.get(typeId) || String(typeId);
  }

  getStatusLabel(statusId: number | null | undefined): string {
    if (statusId === null || statusId === undefined) {
      return '-';
    }
    return this.statusMap.get(statusId) || String(statusId);
  }

  openSnackBar(message: string): void {
    this.snackBar.open(message, '', { duration: 4000 });
  }
}
