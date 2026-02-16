import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectsGeneralSchedulerComponent } from './projects-general-scheduler.component';

describe('ProjectsGeneralSchedulerComponent', () => {
  let component: ProjectsGeneralSchedulerComponent;
  let fixture: ComponentFixture<ProjectsGeneralSchedulerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ProjectsGeneralSchedulerComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProjectsGeneralSchedulerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
