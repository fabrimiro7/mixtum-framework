import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubscriptionEditComponent } from './subscription-edit.component';

describe('SubscriptionEditComponent', () => {
  let component: SubscriptionEditComponent;
  let fixture: ComponentFixture<SubscriptionEditComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SubscriptionEditComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SubscriptionEditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
