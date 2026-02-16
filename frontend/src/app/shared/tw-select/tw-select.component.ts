import { Component, ElementRef, EventEmitter, forwardRef, Input, Output, ViewChild } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-tw-select',
  templateUrl: './tw-select.component.html',
  styleUrls: ['./tw-select.component.css'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => TwSelectComponent),
      multi: true,
    },
  ],
})
export class TwSelectComponent implements ControlValueAccessor {
  @Input() items: any[] = [];
  @Input() bindValue?: string;
  @Input() bindLabel?: string;
  @Input() labelKeys?: string[];
  @Input() placeholder = 'Seleziona...';
  @Input() multiple = false;
  @Input() compareWith?: (a: any, b: any) => boolean;
  @Input() disabled = false;
  @Output() selectionChange = new EventEmitter<{ value: any }>();

  @ViewChild('trigger', { read: ElementRef }) triggerRef?: ElementRef<HTMLElement>;

  open = false;
  activeIndex = -1;
  overlayWidth = 0;

  private value: any = null;
  private onChange: (value: any) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(value: any): void {
    if (this.multiple) {
      this.value = Array.isArray(value) ? value : [];
      return;
    }
    this.value = value;
  }

  registerOnChange(fn: (value: any) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  toggle(): void {
    if (this.disabled) return;
    if (this.open) {
      this.close();
    } else {
      this.openPanel();
    }
  }

  openPanel(): void {
    if (this.disabled) return;
    this.open = true;
    this.setOverlayWidth();
    this.setActiveIndexFromSelection();
  }

  close(): void {
    if (!this.open) return;
    this.open = false;
    this.activeIndex = -1;
    this.onTouched();
  }

  onTriggerKeydown(event: KeyboardEvent): void {
    if (this.disabled) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!this.open) {
          this.openPanel();
          return;
        }
        this.moveActive(1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (!this.open) {
          this.openPanel();
          this.activeIndex = this.items.length - 1;
          return;
        }
        this.moveActive(-1);
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (!this.open) {
          this.openPanel();
          return;
        }
        this.selectActive();
        break;
      case 'Escape':
        if (this.open) {
          event.preventDefault();
          this.close();
        }
        break;
      case 'Tab':
        this.close();
        break;
      default:
        break;
    }
  }

  selectItem(item: any): void {
    if (this.disabled) return;
    const itemValue = this.getItemValue(item);

    if (this.multiple) {
      const values = this.normalizeValueArray(this.value);
      const exists = this.isSelected(item);
      let next: any[];

      if (exists) {
        next = values.filter((value) => !this.isEqual(itemValue, value));
      } else {
        next = [...values, itemValue];
      }

      this.setValue(next);
      return;
    }

    this.setValue(itemValue);
    this.close();
  }

  isSelected(item: any): boolean {
    const itemValue = this.getItemValue(item);

    if (this.multiple) {
      const values = this.normalizeValueArray(this.value);
      return values.some((value) => this.isEqual(itemValue, value));
    }

    return this.isEqual(itemValue, this.value);
  }

  get displayLabel(): string {
    const selectedItems = this.getSelectedItems();

    if (selectedItems.length === 0) {
      if (this.multiple) {
        const values = this.normalizeValueArray(this.value);
        if (values.length > 0) return `${values.length} selezionati`;
      } else if (this.value !== null && this.value !== undefined && this.value !== '') {
        return String(this.value);
      }

      return this.placeholder;
    }

    if (!this.multiple) {
      return this.getItemLabel(selectedItems[0]);
    }

    if (selectedItems.length <= 2) {
      return selectedItems.map((item) => this.getItemLabel(item)).join(', ');
    }

    return `${selectedItems.length} selezionati`;
  }

  get hasSelection(): boolean {
    if (this.getSelectedItems().length > 0) return true;
    if (this.multiple) return this.normalizeValueArray(this.value).length > 0;
    return this.value !== null && this.value !== undefined && this.value !== '';
  }

  setActiveIndex(index: number): void {
    this.activeIndex = index;
  }

  private setValue(value: any): void {
    this.value = value;
    this.onChange(this.value);
    this.selectionChange.emit({ value: this.value });
  }

  private getSelectedItems(): any[] {
    return (this.items || []).filter((item) => this.isSelected(item));
  }

  private getItemValue(item: any): any {
    if (!item) return item;
    if (this.bindValue) return item[this.bindValue];
    return item;
  }

  getItemLabel(item: any): string {
    if (item === null || item === undefined) return '';
    if (this.bindLabel && item[this.bindLabel] !== undefined) return String(item[this.bindLabel]);
    if (this.labelKeys?.length) {
      return this.labelKeys
        .map((key) => this.resolveLabelKey(item, key))
        .filter(Boolean)
        .join(' ');
    }
    if (typeof item === 'string' || typeof item === 'number') return String(item);
    if (item.label !== undefined) return String(item.label);
    if (item.name !== undefined) return String(item.name);
    if (item.title !== undefined) return String(item.title);
    return '';
  }

  private normalizeValueArray(value: any): any[] {
    if (Array.isArray(value)) return value;
    if (value === null || value === undefined) return [];
    return [value];
  }

  private resolveLabelKey(item: any, key: string): any {
    if (!item || !key) return '';
    if (!key.includes('.')) return item[key];
    return key.split('.').reduce((acc, part) => acc?.[part], item);
  }

  private isEqual(a: any, b: any): boolean {
    if (this.compareWith && !this.bindValue) {
      return this.compareWith(a, b);
    }
    return a === b;
  }

  private setOverlayWidth(): void {
    const trigger = this.triggerRef?.nativeElement;
    if (!trigger) return;
    this.overlayWidth = trigger.getBoundingClientRect().width;
  }

  private setActiveIndexFromSelection(): void {
    const selectedIndex = (this.items || []).findIndex((item) => this.isSelected(item));
    if (selectedIndex >= 0) {
      this.activeIndex = selectedIndex;
    } else {
      this.activeIndex = this.items.length > 0 ? 0 : -1;
    }
  }

  private moveActive(delta: number): void {
    if (!this.items?.length) return;
    const next = (this.activeIndex + delta + this.items.length) % this.items.length;
    this.activeIndex = next;
  }

  private selectActive(): void {
    if (this.activeIndex < 0 || this.activeIndex >= this.items.length) return;
    this.selectItem(this.items[this.activeIndex]);
  }
}
