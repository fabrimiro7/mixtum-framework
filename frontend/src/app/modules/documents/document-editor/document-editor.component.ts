import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { catchError, forkJoin, of } from 'rxjs';

import { DocumentsApiService } from 'src/app/services/api/documents-api.service';
import { Document, DocumentBlock, DocumentStatus, DocumentType } from 'src/app/models/document';
import { NotionBlock } from 'src/app/shared/notion-block-editor/notion-block.model';
import { blockTitleFromContent, extractEditableContent, inferBlockTypeFromHtml, serializeBlockToHtml } from 'src/app/shared/notion-block-editor/notion-block.utils';

@Component({
  selector: 'app-document-editor',
  templateUrl: './document-editor.component.html',
  styleUrls: ['./document-editor.component.css']
})
export class DocumentEditorComponent implements OnInit {
  documentId = 0;
  document: Document | null = null;
  statuses: DocumentStatus[] = [];
  types: DocumentType[] = [];
  documentForm: UntypedFormGroup;
  renderedHtml: SafeHtml | null = null;
  renderedRaw = '';
  loading = false;
  saving = false;
  savingBlocks = false;
  blocks: NotionBlock[] = [];

  constructor(
    private route: ActivatedRoute,
    private fb: UntypedFormBuilder,
    private documentsApi: DocumentsApiService,
    private snackBar: MatSnackBar,
    private sanitizer: DomSanitizer,
  ) {
    this.documentForm = this.fb.group({
      title: ['', [Validators.required, Validators.maxLength(255)]],
      status: [null, Validators.required],
      type: [null, Validators.required],
      context_snapshot: ['{}'],
    });
  }

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      this.documentId = Number(params.get('id') || 0);
      this.loadFilters();
      this.loadDocument();
    });
  }

  loadFilters(): void {
    this.documentsApi.listStatuses()
      .pipe(catchError(() => of([] as DocumentStatus[])))
      .subscribe((data: DocumentStatus[]) => {
        this.statuses = data;
      });

    this.documentsApi.listTypes()
      .pipe(catchError(() => of([] as DocumentType[])))
      .subscribe((data: DocumentType[]) => {
        this.types = data;
      });
  }

  loadDocument(): void {
    if (!this.documentId) {
      return;
    }
    this.loading = true;
    this.documentsApi.getDocument(this.documentId)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel caricamento del documento.');
          this.loading = false;
          return of(null);
        })
      )
      .subscribe((doc: Document | null) => {
        if (!doc) {
          this.loading = false;
          return;
        }
        this.document = doc;
        this.documentForm.patchValue({
          title: doc.title,
          status: doc.status,
          type: doc.type,
          context_snapshot: JSON.stringify(doc.context_snapshot || {}, null, 2),
        });
        this.blocks = this.buildBlocksFromDocument(doc.blocks || []);
        if (doc.rendered_html) {
          this.renderedRaw = doc.rendered_html;
          this.renderedHtml = this.sanitizer.bypassSecurityTrustHtml(doc.rendered_html);
        }
        if (!doc.is_editable) {
          this.documentForm.disable();
        } else {
          this.documentForm.enable();
        }
        this.loading = false;
      });
  }

  buildBlocksFromDocument(blocks: DocumentBlock[]): NotionBlock[] {
    return blocks.map((block) => {
      const type = inferBlockTypeFromHtml(block.content || '');
      return {
        id: block.id,
        type,
        content: extractEditableContent(block.content || '', type),
        title: block.title,
        position: block.position,
      };
    });
  }

  saveDocument(): void {
    const titleCtrl = this.documentForm.get('title');
    const statusCtrl = this.documentForm.get('status');
    const typeCtrl = this.documentForm.get('type');

    if (!this.documentId || titleCtrl?.invalid || statusCtrl?.invalid || typeCtrl?.invalid) {
      titleCtrl?.markAsTouched();
      statusCtrl?.markAsTouched();
      typeCtrl?.markAsTouched();
      return;
    }

    let contextSnapshot: any = {};
    try {
      const rawValue = this.documentForm.getRawValue();
      contextSnapshot = JSON.parse(rawValue.context_snapshot || '{}');
    } catch {
      this.openSnackBar('Il JSON del contesto non e\u00e8 valido.');
      return;
    }

    const payload = {
      title: this.documentForm.get('title')?.value,
      status: this.documentForm.get('status')?.value,
      type: this.documentForm.get('type')?.value,
      context_snapshot: contextSnapshot,
    };

    this.saving = true;
    this.documentsApi.updateDocument(this.documentId, payload)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel salvataggio del documento.');
          this.saving = false;
          return of(null);
        })
      )
      .subscribe((doc: Document | null) => {
        if (doc) {
          this.document = doc;
          this.openSnackBar('Documento salvato.');
        }
        this.saving = false;
      });
  }

  saveBlocks(): void {
    if (!this.document || !this.document.is_editable) {
      return;
    }
    if (this.blocks.length === 0) {
      return;
    }
    this.savingBlocks = true;

    const orderedBlocks = this.blocks.map((block, index) => ({ ...block, position: index }));

    const updates = orderedBlocks
      .filter(block => !!block.id)
      .map((block) => {
        const html = serializeBlockToHtml(block);
        return this.documentsApi.updateDocumentBlock(block.id as number, {
          title: blockTitleFromContent(block),
          content: html,
          position: block.position,
        });
      });

    const creates = orderedBlocks
      .filter(block => !block.id)
      .map((block) => {
        const html = serializeBlockToHtml(block);
        return this.documentsApi.createDocumentBlock({
          document: this.documentId,
          title: blockTitleFromContent(block),
          content: html,
          position: block.position,
        });
      });

    forkJoin([...updates, ...creates])
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel salvataggio dei blocchi.');
          this.savingBlocks = false;
          return of([]);
        })
      )
      .subscribe(() => {
        this.openSnackBar('Blocchi salvati.');
        this.savingBlocks = false;
        this.loadDocument();
      });
  }

  onBlockDeleted(blockId: number): void {
    if (!blockId) {
      return;
    }
    this.documentsApi.deleteDocumentBlock(blockId)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nella rimozione del blocco.');
          return of(null);
        })
      )
      .subscribe();
  }

  renderDocument(): void {
    if (!this.documentId) {
      return;
    }
    this.documentsApi.renderDocument(this.documentId)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel render.');
          return of(null);
        })
      )
      .subscribe((data: any) => {
        if (!data?.rendered_html) {
          return;
        }
        this.renderedRaw = data.rendered_html;
        this.renderedHtml = this.sanitizer.bypassSecurityTrustHtml(data.rendered_html);
      });
  }

  freezeDocument(): void {
    if (!this.documentId) {
      return;
    }
    this.documentsApi.freezeDocument(this.documentId)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel freeze.');
          return of(null);
        })
      )
      .subscribe((doc: Document | null) => {
        if (doc) {
          this.document = doc;
          this.documentForm.disable();
          this.openSnackBar('Documento congelato.');
        }
      });
  }

  openSnackBar(message: string): void {
    this.snackBar.open(message, '', { duration: 4000 });
  }
}
