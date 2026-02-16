import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DocumentsListComponent } from './documents-list/documents-list.component';
import { DocumentEditorComponent } from './document-editor/document-editor.component';
import { DocumentCreateComponent } from './document-create/document-create.component';
import { TemplatesListComponent } from './templates-list/templates-list.component';
import { TemplateEditorComponent } from './template-editor/template-editor.component';

const routes: Routes = [
  { path: '', component: DocumentsListComponent, data: { breadcrumb: 'Documenti' } },
  { path: 'new', component: DocumentCreateComponent, data: { breadcrumb: 'Nuovo Documento' } },
  { path: 'templates', component: TemplatesListComponent, data: { breadcrumb: 'Template' } },
  { path: 'templates/:id', component: TemplateEditorComponent, data: { breadcrumb: 'Modifica Template' } },
  { path: ':id', component: DocumentEditorComponent, data: { breadcrumb: 'Editor Documento' } },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DocumentsRoutingModule { }
