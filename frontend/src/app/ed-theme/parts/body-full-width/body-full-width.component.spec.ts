import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BodyFullWidthComponent } from './body-full-width.component';

describe('BodyFullWidthComponent', () => {
  let component: BodyFullWidthComponent;
  let fixture: ComponentFixture<BodyFullWidthComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BodyFullWidthComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BodyFullWidthComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
