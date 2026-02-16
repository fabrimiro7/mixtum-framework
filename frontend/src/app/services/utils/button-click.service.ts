import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ButtonClickService {
  private clickSubject = new Subject<void>();

  clickButton() {
    this.clickSubject.next();
  }

  get clickEvent$() {
    return this.clickSubject.asObservable();
  }
}