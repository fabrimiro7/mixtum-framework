import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, forkJoin, of } from 'rxjs';

import { DocumentsApiService } from 'src/app/services/api/documents-api.service';
import { Block, DocumentTemplate, DocumentTemplateBlock } from 'src/app/models/document';
import { NotionBlock } from 'src/app/shared/notion-block-editor/notion-block.model';
import { blockTitleFromContent, extractEditableContent, inferBlockTypeFromHtml, serializeBlockToHtml } from 'src/app/shared/notion-block-editor/notion-block.utils';

@Component({
  selector: 'app-template-editor',
  templateUrl: './template-editor.component.html',
  styleUrls: ['./template-editor.component.css']
})
export class TemplateEditorComponent implements OnInit {
  templateId = 0;
  template: DocumentTemplate | null = null;
  templateForm: UntypedFormGroup;
  blocksLibrary: Block[] = [];
  selectedLibraryBlockId: number | null = null;
  newBlockForm: UntypedFormGroup;
  savingBlocks = false;
  templateBlocks: Array<NotionBlock & { sourceBlockId?: number }> = [];

  constructor(
    private route: ActivatedRoute,
    private fb: UntypedFormBuilder,
    private documentsApi: DocumentsApiService,
    private snackBar: MatSnackBar,
  ) {
    this.templateForm = this.fb.group({
      title: ['', [Validators.required, Validators.maxLength(255)]],
      description: [''],
    });
    this.newBlockForm = this.fb.group({
      title: ['', Validators.required],
      content: ['', Validators.required],
    });
  }

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      this.templateId = Number(params.get('id') || 0);
      this.loadTemplate();
      this.loadBlocksLibrary();
    });
  }

  loadTemplate(): void {
    if (!this.templateId) {
      return;
    }
    this.documentsApi.getTemplate(this.templateId)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel caricamento template.');
          return of(null);
        })
      )
      .subscribe((tpl: DocumentTemplate | null) => {
        if (!tpl) {
          return;
        }
        this.template = tpl;
        this.templateForm.patchValue({
          title: tpl.title,
          description: tpl.description || '',
        });
        this.templateBlocks = this.buildTemplateBlocks(tpl.template_blocks || []);
      });
  }

  buildTemplateBlocks(blocks: DocumentTemplateBlock[]): Array<NotionBlock & { sourceBlockId?: number }> {
    return blocks.map((block) => {
      const type = inferBlockTypeFromHtml(block.content_snapshot || '');
      return {
        id: block.id,
        type,
        content: extractEditableContent(block.content_snapshot || '', type),
        title: block.title_snapshot,
        position: block.position,
        sourceBlockId: block.block,
      };
    });
  }

  saveTemplate(): void {
    if (this.templateForm.invalid || !this.templateId) {
      this.templateForm.markAllAsTouched();
      return;
    }
    const payload = {
      title: this.templateForm.value.title,
      description: this.templateForm.value.description,
    };
    this.documentsApi.updateTemplate(this.templateId, payload)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel salvataggio template.');
          return of(null);
        })
      )
      .subscribe(() => {
        this.openSnackBar('Template salvato.');
      });
  }

  saveTemplateBlocks(): void {
    if (this.templateBlocks.length === 0) {
      return;
    }
    this.savingBlocks = true;
    const orderedBlocks = this.templateBlocks.map((block, index) => ({ ...block, position: index }));
    const calls = orderedBlocks
      .filter(block => !!block.id)
      .map((block) => {
        return this.documentsApi.updateTemplateBlock(block.id as number, {
          title_snapshot: blockTitleFromContent(block),
          content_snapshot: serializeBlockToHtml(block),
          position: block.position,
        });
      });
    forkJoin(calls)
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
        this.loadTemplate();
      });
  }

  addTemplateBlock(): void {
    if (!this.selectedLibraryBlockId || !this.templateId) {
      return;
    }
    this.documentsApi.addTemplateBlock(this.templateId, {
      block: this.selectedLibraryBlockId,
    })
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nell\'aggiunta blocco.');
          return of(null);
        })
      )
      .subscribe((block: DocumentTemplateBlock | null) => {
        this.selectedLibraryBlockId = null;
        if (block) {
          const type = inferBlockTypeFromHtml(block.content_snapshot || '');
          this.templateBlocks.push({
            id: block.id,
            type,
            content: extractEditableContent(block.content_snapshot || '', type),
            title: block.title_snapshot,
            position: block.position,
            sourceBlockId: block.block,
          });
        } else {
          this.loadTemplate();
        }
      });
  }

  onTemplateBlockDeleted(blockId: number): void {
    if (!blockId) {
      return;
    }
    this.documentsApi.deleteTemplateBlock(blockId)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nella rimozione del blocco.');
          return of(null);
        })
      )
      .subscribe(() => {
        this.templateBlocks = this.templateBlocks.filter(block => block.id !== blockId);
      });
  }

  loadBlocksLibrary(): void {
    this.documentsApi.listBlocks()
      .pipe(catchError(() => of([] as Block[])))
      .subscribe((blocks: Block[]) => {
        this.blocksLibrary = blocks;
      });
  }

  createBlock(): void {
    if (this.newBlockForm.invalid) {
      this.newBlockForm.markAllAsTouched();
      return;
    }
    this.documentsApi.createBlock(this.newBlockForm.value)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nella creazione del blocco.');
          return of(null);
        })
      )
      .subscribe((block: Block | null) => {
        if (block) {
          this.newBlockForm.reset();
          this.loadBlocksLibrary();
        }
      });
  }

  saveLibraryBlock(block: Block): void {
    this.documentsApi.updateBlock(block.id, {
      title: block.title,
      content: block.content,
      is_active: block.is_active,
    })
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nel salvataggio del blocco.');
          return of(null);
        })
      )
      .subscribe(() => {
        this.openSnackBar('Blocco salvato.');
      });
  }

  deleteLibraryBlock(block: Block): void {
    this.documentsApi.deleteBlock(block.id)
      .pipe(
        catchError(() => {
          this.openSnackBar('Errore nella rimozione del blocco.');
          return of(null);
        })
      )
      .subscribe(() => {
        this.loadBlocksLibrary();
      });
  }

  openSnackBar(message: string): void {
    this.snackBar.open(message, '', { duration: 4000 });
  }
}
