import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsertEmailComponent } from './insert-email.component';

describe('InsertEmailComponent', () => {
  let component: InsertEmailComponent;
  let fixture: ComponentFixture<InsertEmailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ InsertEmailComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsertEmailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
