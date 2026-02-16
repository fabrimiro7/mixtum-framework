import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { OverlayModule } from '@angular/cdk/overlay';

import { RichTextEditorComponent } from './rich-text-editor/rich-text-editor.component';
import { WorkspaceSelectorComponent } from './workspace-selector/workspace-selector.component';
import { NotionBlockEditorComponent } from './notion-block-editor/notion-block-editor.component';
import { TwSelectComponent } from './tw-select/tw-select.component';

@NgModule({
  declarations: [
    RichTextEditorComponent,
    WorkspaceSelectorComponent,
    NotionBlockEditorComponent,
    TwSelectComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    DragDropModule,
    OverlayModule,
  ],
  exports: [
    RichTextEditorComponent,
    WorkspaceSelectorComponent,
    NotionBlockEditorComponent,
    TwSelectComponent,
  ]
})
export class SharedModule { }
