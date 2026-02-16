import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { of } from 'rxjs';
import { ProjectDetailsComponent } from './project-details.component';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { LinkApiService } from 'src/app/services/api/link-api.service';
import { DateParser } from 'src/app/util/date_parse';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { ReactiveFormsModule } from '@angular/forms';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { SprintApiService } from 'src/app/services/api/sprint-api.service';

class ProjectApiServiceStub {
  projectDetail() {
    return of({ insert_date: '2024-01-01' });
  }
}

class LinkApiServiceStub {
  list() {
    return of([]);
  }
  create() {
    return of({});
  }
  update() {
    return of({});
  }
  delete() {
    return of({});
  }
  getContentTypeId() {
    return of(1);
  }
}

class TicketApiServiceStub {
  getProjectTasks() {
    return of([]);
  }
  updateTask() {
    return of({ status: 'todo', status_display: 'To Do' });
  }
}

class SprintApiServiceStub {
  getProjectPhases() {
    return of([]);
  }
  updatePhase() {
    return of({});
  }
}

class DateParserStub {
  ISOToNormalDate(value: any) {
    return value;
  }
}

describe('ProjectDetailsComponent', () => {
  let component: ProjectDetailsComponent;
  let fixture: ComponentFixture<ProjectDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        RouterTestingModule,
        MatSnackBarModule,
        ReactiveFormsModule,
        DragDropModule,
      ],
      declarations: [ ProjectDetailsComponent ],
      providers: [
        { provide: ActivatedRoute, useValue: { paramMap: of(convertToParamMap({ id: '1' })), queryParamMap: of(convertToParamMap({})) } },
        { provide: ProjectApiService, useClass: ProjectApiServiceStub },
        { provide: LinkApiService, useClass: LinkApiServiceStub },
        { provide: TicketApiService, useClass: TicketApiServiceStub },
        { provide: SprintApiService, useClass: SprintApiServiceStub },
        { provide: DateParser, useClass: DateParserStub },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProjectDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
