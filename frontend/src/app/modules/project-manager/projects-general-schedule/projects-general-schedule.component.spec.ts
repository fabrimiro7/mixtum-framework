import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectsGeneralScheduleComponent } from './projects-general-schedule.component';

describe('ProjectsGeneralScheduleComponent', () => {
  let component: ProjectsGeneralScheduleComponent;
  let fixture: ComponentFixture<ProjectsGeneralScheduleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ProjectsGeneralScheduleComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProjectsGeneralScheduleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
