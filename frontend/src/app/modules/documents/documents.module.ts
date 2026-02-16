import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DragDropModule } from '@angular/cdk/drag-drop';

import { DocumentsRoutingModule } from './documents-routing.module';
import { DocumentsListComponent } from './documents-list/documents-list.component';
import { DocumentEditorComponent } from './document-editor/document-editor.component';
import { DocumentCreateComponent } from './document-create/document-create.component';
import { TemplatesListComponent } from './templates-list/templates-list.component';
import { TemplateEditorComponent } from './template-editor/template-editor.component';
import { SharedModule } from 'src/app/shared/shared.module';

@NgModule({
  declarations: [
    DocumentsListComponent,
    DocumentEditorComponent,
    DocumentCreateComponent,
    TemplatesListComponent,
    TemplateEditorComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    DocumentsRoutingModule,
    DragDropModule,
    SharedModule,
  ]
})
export class DocumentsModule { }
