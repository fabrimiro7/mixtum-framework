import { Component, EventEmitter, forwardRef, Input, Output } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { NotionBlock, NotionBlockType, NOTION_BLOCK_TYPES } from './notion-block.model';

@Component({
  selector: 'app-notion-block-editor',
  templateUrl: './notion-block-editor.component.html',
  styleUrls: ['./notion-block-editor.component.css'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => NotionBlockEditorComponent),
      multi: true,
    }
  ]
})
export class NotionBlockEditorComponent implements ControlValueAccessor {
  @Input() disabled = false;
  @Input() allowInsert = true;
  @Output() blockDeleted = new EventEmitter<number>();

  blocks: NotionBlock[] = [];
  blockTypes = NOTION_BLOCK_TYPES;
  insertMenuIndex: number | null = null;
  slashMenuIndex: number | null = null;

  private onChange: (value: NotionBlock[]) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(value: NotionBlock[] | null): void {
    this.blocks = Array.isArray(value) ? value.map(b => ({ ...b })) : [];
  }

  registerOnChange(fn: (value: NotionBlock[]) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  drop(event: CdkDragDrop<NotionBlock[]>): void {
    moveItemInArray(this.blocks, event.previousIndex, event.currentIndex);
    this.emitChange();
  }

  toggleInsertMenu(index: number): void {
    if (!this.allowInsert || this.disabled) {
      return;
    }
    this.insertMenuIndex = this.insertMenuIndex === index ? null : index;
  }

  addFirstBlock(): void {
    if (this.disabled) {
      return;
    }
    this.blocks = [{ id: null, type: 'paragraph', content: '' }];
    this.emitChange();
  }

  insertBlock(index: number, type: NotionBlockType): void {
    if (this.disabled) {
      return;
    }
    const newBlock: NotionBlock = {
      id: null,
      type,
      content: '',
    };
    this.blocks.splice(index + 1, 0, newBlock);
    this.insertMenuIndex = null;
    this.emitChange();
  }

  deleteBlock(index: number): void {
    if (this.disabled) {
      return;
    }
    const removed = this.blocks.splice(index, 1);
    if (removed.length && removed[0].id) {
      this.blockDeleted.emit(removed[0].id as number);
    }
    this.emitChange();
  }

  setBlockType(index: number, type: NotionBlockType, fromSlash = false): void {
    const block = this.blocks[index];
    block.type = type;
    if (type === 'divider') {
      block.content = '';
    }
    if (fromSlash) {
      block.content = block.content.replace(/^\s*\//, '').trim();
      this.slashMenuIndex = null;
    }
    this.emitChange();
  }

  onBlockInput(index: number, event: Event): void {
    const block = this.blocks[index];
    if (block.type === 'divider') {
      return;
    }
    const el = event.target as HTMLElement | null;
    if (!el) {
      return;
    }
    if (block.type === 'bulleted' || block.type === 'numbered') {
      block.content = (el.textContent || '').replace(/\u00a0/g, ' ');
    } else {
      block.content = el.innerHTML || '';
    }
    this.slashMenuIndex = block.content.trim().startsWith('/') ? index : null;
    this.emitChange();
  }

  displayContent(block: NotionBlock): string {
    if (block.type === 'bulleted' || block.type === 'numbered') {
      return (block.content || '').replace(/\n/g, '<br>');
    }
    return block.content || '';
  }

  placeholderFor(block: NotionBlock): string {
    switch (block.type) {
      case 'heading1':
        return 'Titolo grande';
      case 'heading2':
        return 'Titolo';
      case 'quote':
        return 'Citazione';
      case 'bulleted':
        return 'Elemento lista (uno per riga)';
      case 'numbered':
        return 'Elemento lista numerata (uno per riga)';
      default:
        return 'Scrivi qualcosa...';
    }
  }

  private emitChange(): void {
    this.onChange(this.blocks.map(b => ({ ...b })));
  }

  touch(): void {
    this.onTouched();
  }
}
