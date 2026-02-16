import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TicketsByPeriodComponent } from './tickets-by-period.component';

describe('TicketsByPeriodComponent', () => {
  let component: TicketsByPeriodComponent;
  let fixture: ComponentFixture<TicketsByPeriodComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TicketsByPeriodComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TicketsByPeriodComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
