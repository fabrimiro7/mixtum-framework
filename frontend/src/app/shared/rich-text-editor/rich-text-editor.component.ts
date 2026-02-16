import { AfterViewInit, Component, ElementRef, forwardRef, Input, ViewChild } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-rich-text-editor',
  templateUrl: './rich-text-editor.component.html',
  styleUrls: ['./rich-text-editor.component.css'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => RichTextEditorComponent),
      multi: true,
    },
  ],
})
export class RichTextEditorComponent implements ControlValueAccessor, AfterViewInit {
  @Input() placeholder = '';
  @Input() disabled = false;

  @ViewChild('editor') editor!: ElementRef<HTMLDivElement>;

  value = '';
  private viewInitialized = false;
  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};
  showLinkForm = false;
  linkUrl = '';
  linkLabel = '';

  ngAfterViewInit(): void {
    this.viewInitialized = true;
    this.syncEditorWithValue();
  }

  writeValue(value: string): void {
    this.value = value ?? '';
    this.syncEditorWithValue();
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  format(command: string): void {
    if (this.disabled) {
      return;
    }
    this.focusEditor();
    document.execCommand(command, false);
    this.emitChange();
  }

  onLinkUrlInput(event: Event): void {
    const target = event.target as HTMLInputElement | null;
    this.linkUrl = target?.value ?? '';
  }

  onLinkLabelInput(event: Event): void {
    const target = event.target as HTMLInputElement | null;
    this.linkLabel = target?.value ?? '';
  }

  toggleLinkForm(): void {
    if (this.disabled) {
      return;
    }
    this.showLinkForm = !this.showLinkForm;
    if (!this.showLinkForm) {
      this.resetLinkInputs();
    } else {
      setTimeout(() => this.focusEditor());
    }
  }

  applyLink(): void {
    if (this.disabled) {
      return;
    }

    const urlValue = this.linkUrl.trim();
    if (!urlValue) {
      return;
    }

    const labelValue = this.linkLabel.trim() || urlValue;
    const formattedUrl = urlValue.toLowerCase().startsWith('http') ? urlValue : `http://${urlValue}`;
    const anchor = `<a href="${formattedUrl}" target="_blank" rel="noopener noreferrer">${labelValue}</a>`;

    this.focusEditor();
    document.execCommand('insertHTML', false, anchor);
    this.emitChange();
    this.resetLinkInputs();
    this.showLinkForm = false;
  }

  cancelLink(): void {
    this.resetLinkInputs();
    this.showLinkForm = false;
  }

  private resetLinkInputs(): void {
    this.linkUrl = '';
    this.linkLabel = '';
  }

  onInput(): void {
    this.emitChange();
  }

  onPaste(event: ClipboardEvent): void {
    event.preventDefault();
    const text = event.clipboardData?.getData('text/plain') ?? '';
    document.execCommand('insertText', false, text);
  }

  touch(): void {
    this.onTouched();
  }

  hasContent(): boolean {
    if (!this.editor) {
      return this.value?.trim().length > 0;
    }

    const strippedText = (this.editor.nativeElement.textContent ?? '').trim();
    return strippedText.length > 0 || /<(b|strong|u|i|br)[\s/>]/i.test(this.editor.nativeElement.innerHTML);
  }

  private emitChange(): void {
    if (!this.editor) {
      return;
    }
    const newValue = this.editor.nativeElement.innerHTML;
    this.value = newValue;
    this.onChange(this.value);
  }

  private focusEditor(): void {
    this.editor?.nativeElement.focus();
  }

  private syncEditorWithValue(): void {
    if (!this.viewInitialized || !this.editor) {
      return;
    }
    this.editor.nativeElement.innerHTML = this.value;
  }
}
