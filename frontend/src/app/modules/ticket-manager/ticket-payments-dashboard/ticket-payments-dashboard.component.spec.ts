import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TicketPaymentsDashboardComponent } from './ticket-payments-dashboard.component';

describe('TicketPaymentsDashboardComponent', () => {
  let component: TicketPaymentsDashboardComponent;
  let fixture: ComponentFixture<TicketPaymentsDashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TicketPaymentsDashboardComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TicketPaymentsDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
